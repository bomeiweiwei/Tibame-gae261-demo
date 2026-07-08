# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Standalone tool that converts resort knowledge-base PDFs into vectors and uploads them to Qdrant Cloud, plus test scripts for RAG search and itinerary recommendation. There is no test suite, build step, or web server — every script is a runnable CLI entrypoint invoked directly with `python <file>.py`.

## Commands

```bash
pip install -r requirements.txt        # install dependencies

python build_qdrant_vector_db.py       # embed knowledges/*.pdf and upload to Qdrant Cloud
python create_indexes.py               # create payload indexes on the Qdrant collection
python app_qdrant.py                   # test: category-filtered RAG search
python app_qdrant2.py                  # test: itinerary recommendation (requires SQL Server)
python sync_knowledge_to_db.py         # extract PDF text via local LLM, write to SQL Server
```

Config lives in `.env` (copy from `.env.example`). Every script calls `load_dotenv()` and a `validate_env()` guard that raises `ValueError` on missing `QDRANT_URL` / `QDRANT_API_KEY` / `QDRANT_COLLECTION_NAME`.

`QDRANT_FORCE_RECREATE=true` (the default) causes `build_qdrant_vector_db.py` to **delete and recreate** the collection on every run — be deliberate about this when testing against a shared collection.

## Architecture

**Ingestion pipeline** (`build_qdrant_vector_db.py`): loads every PDF in `knowledges/` via `PyPDFLoader` → splits with `RecursiveCharacterTextSplitter` (chunk_size=500, overlap=80) → embeds in batches of `QDRANT_BATCH_SIZE` → upserts into a Qdrant collection with deterministic point IDs (`uuid5` over source file + page + chunk index + content, so re-running is idempotent for unchanged content).

**PDF filename convention drives metadata**: files must be named `{location_scope}-{category}-{place_name}.pdf` (e.g. `內部-戶外景點-彩虹天梯.pdf`). `parse_pdf_filename()` (duplicated in `build_qdrant_vector_db.py` and `sync_knowledge_to_db.py`) splits on `-` (maxsplit=2) into `location_scope` / `category` / `place_name`, stored as point payload metadata and used later for Qdrant filter queries. Files that don't match the 3-part pattern fall back to `未分類`.

**Embedding provider abstraction** (`embedding_factory.py`): `get_embedding_function()` switches on `EMBEDDING_PROVIDER` (`azure` or `gemini`) and returns a LangChain `Embeddings` instance — `OpenAIEmbeddings` pointed at an Azure endpoint, or a custom `GeminiEmbeddings` class wrapping Vertex AI's `genai.Client`. All services that need embeddings (search, ingestion) go through this one factory so the provider can be swapped via env var alone.

**Two independent read paths on top of the same Qdrant collection**, both built on `langchain_qdrant.QdrantVectorStore.from_existing_collection`:
- `rag_search_service.py` — `RagSearchService.search_knowledge_by_categories()` builds a category-aware query prompt (listing 名稱/特色/說明/適合族群/營業時間/注意事項/價格/服務內容 as retrieval hints) and filters by `metadata.category` via `MatchAny`. Exposed as a singleton through `get_rag_search_service()` (`@lru_cache`).
- `itinerary_knowledge_service.py` — `ItineraryKnowledgeService.build_itinerary_by_dates()` runs a fixed set of time-slotted searches (09:00/11:00/13:00/15:00/18:00, defined in `_get_search_plans()`) against the vector store, deduplicates by `place_name` within a day, then cross-references each hit's `source_file` against SQL Server (`ResortKnowledgeItem` table) via `pyodbc` to pull the canonical place/category/feature text.

**`create_indexes.py`** must be run before filter-based queries work reliably on Qdrant Cloud — it creates KEYWORD payload indexes on `metadata.category`, `metadata.location_scope`, `metadata.place_name`, `metadata.source_file`. It's idempotent (catches "already exists" errors and continues).

**`sync_knowledge_to_db.py`** is a separate, one-way pipeline unrelated to Qdrant: it extracts raw PDF text (`pypdf`), asks a local LLM (LM Studio via `ChatOpenAI`, only `LMSTUDIO` provider implemented) to summarize a 30-character "feature" description per place, and MERGEs (upsert) the result into the SQL Server `ResortKnowledgeItem` table keyed by `SourceFile`. This table is what `itinerary_knowledge_service.py` reads back from at recommendation time — so the two pipelines (vector DB build vs. SQL sync) must both be kept up to date when `knowledges/` changes, or itinerary lookups will silently skip places missing from the DB (`_get_knowledge_item_by_source_file` returns `None` and the place is dropped).

## Environment variables

See `.env.example` for the full list. Key groups:
- `PDF_DIR` — source PDF directory (default `knowledges`)
- `EMBEDDING_PROVIDER` (`azure` | `gemini`) plus the corresponding `AZURE_OPENAI_*` or `GOOGLE_*`/`GEMINI_*` credentials
- `DB_SERVER`/`DB_NAME`/`DB_USER`/`DB_PASSWORD` — SQL Server, used only by `itinerary_knowledge_service.py` and `sync_knowledge_to_db.py`
- `LLM_PROVIDER`/`LMSTUDIO_*` — local LLM used only by `sync_knowledge_to_db.py`
- `QDRANT_URL`/`QDRANT_API_KEY`/`QDRANT_COLLECTION_NAME`/`QDRANT_BATCH_SIZE`/`QDRANT_TIMEOUT_SECONDS`/`QDRANT_FORCE_RECREATE`
