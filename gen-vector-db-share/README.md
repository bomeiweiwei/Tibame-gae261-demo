# gen-vector-db

將渡假村知識庫 PDF 轉換為向量並上傳至 Qdrant Cloud 的獨立工具，並提供 RAG 檢索與行程推薦測試腳本。

## 功能概覽

- **建立向量資料庫**：讀取 `knowledges/` 目錄下的 PDF，切分文字、產生 embedding，並上傳至 Qdrant Cloud collection。
- **Payload Index**：為常用的 metadata 欄位（category、location_scope、place_name、source_file）建立 index，加速 filter 查詢。
- **RAG 檢索測試**：依據分類（category）過濾並搜尋知識庫，回傳相關內容與分數。
- **行程推薦測試**：依時段（09:00 ~ 18:00）搜尋合適的景點/餐廳，並比對 SQL Server 中的知識明細，組成每日行程。
- **知識庫同步至資料庫**：讀取 PDF 全文，透過 LLM（LM Studio）萃取景點特色，寫入 SQL Server 的 `ResortKnowledgeItem` 資料表。

## 專案結構

| 檔案 | 說明 |
| --- | --- |
| `build_qdrant_vector_db.py` | 讀取 PDF → 切分 chunk → 產生 embedding → 上傳至 Qdrant Cloud（可設定強制重建 collection）|
| `create_indexes.py` | 為 Qdrant collection 建立 payload index（metadata 欄位）|
| `embedding_factory.py` | Embedding 供應商工廠，支援 Azure OpenAI 與 Gemini（Vertex AI）|
| `rag_search_service.py` | 依 category 過濾搜尋 Qdrant 知識庫的服務類別 |
| `itinerary_knowledge_service.py` | 依時段搜尋景點/餐廳並比對 SQL Server 產生每日行程 |
| `sync_knowledge_to_db.py` | 解析 PDF 全文，透過 LLM 萃取特色描述，寫入 SQL Server |
| `app_qdrant.py` | RAG 檢索測試腳本 |
| `app_qdrant2.py` | 行程推薦測試腳本 |
| `knowledges/` | 知識庫 PDF 來源檔案 |

## PDF 檔名規則

檔名格式：`內部或外部-類別-景點名稱.pdf`

範例：`內部-戶外景點-彩虹天梯.pdf`

程式會依 `-` 切分出：
- `location_scope`（內部 / 外部）
- `category`（類別）
- `place_name`（景點名稱）

並存入向量資料的 metadata 中，供後續 filter 查詢使用。

## 環境設定

1. 安裝相依套件：

   ```bash
   pip install -r requirements.txt
   ```

2. 複製 `.env.example` 為 `.env`，並依需求填入以下設定：

   | 變數 | 說明 |
   | --- | --- |
   | `PDF_DIR` | PDF 知識庫來源目錄（預設 `knowledges`）|
   | `EMBEDDING_PROVIDER` | `azure` 或 `gemini` |
   | `AZURE_OPENAI_ENDPOINT` / `AZURE_OPENAI_API_KEY` / `AZURE_OPENAI_API_VERSION` / `AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME` | Azure OpenAI Embedding 設定 |
   | `GOOGLE_APPLICATION_CREDENTIALS` / `GOOGLE_CLOUD_PROJECT` / `GOOGLE_CLOUD_LOCATION` / `GEMINI_EMBEDDING_MODEL` | Gemini（Vertex AI）Embedding 設定 |
   | `DB_SERVER` / `DB_NAME` / `DB_USER` / `DB_PASSWORD` | SQL Server 連線設定（行程推薦與知識同步用）|
   | `LLM_PROVIDER` / `LMSTUDIO_MODEL_NAME` / `LMSTUDIO_BASE_URL` / `LMSTUDIO_API_KEY` | LLM 設定，用於萃取景點特色（目前僅支援 `lmstudio`）|
   | `QDRANT_URL` / `QDRANT_API_KEY` | Qdrant Cloud 連線資訊 |
   | `QDRANT_COLLECTION_NAME` | Collection 名稱（預設 `resort_knowledge`）|
   | `QDRANT_BATCH_SIZE` | 每批上傳筆數（預設 30）|
   | `QDRANT_TIMEOUT_SECONDS` | Qdrant client timeout 秒數（預設 180）|
   | `QDRANT_FORCE_RECREATE` | 是否在每次執行時刪除並重建 collection（預設 `true`，正式環境請小心使用）|

## 使用方式

### 1. 建立 / 更新向量資料庫

將 `knowledges/` 目錄下的 PDF 全部向量化並上傳到 Qdrant Cloud：

```bash
python build_qdrant_vector_db.py
```

> 注意：`QDRANT_FORCE_RECREATE=true` 時會先刪除既有 collection 再重建，執行前請確認是否為預期行為。

### 2. 建立 Payload Index

首次建立 collection 或需要 filter 查詢時，建立 metadata 欄位的 index：

```bash
python create_indexes.py
```

### 3. 測試 RAG 檢索

```bash
python app_qdrant.py
```

會依 category 分類搜尋知識庫並印出 JSON 格式結果。

### 4. 測試行程推薦

```bash
python app_qdrant2.py
```

依指定日期（`date_list`）搜尋各時段（09:00、11:00、13:00、15:00、18:00）合適的景點與餐廳，並比對 SQL Server 資料組成每日行程。

### 5. 同步知識庫特色描述至資料庫

透過 LM Studio 本地 LLM 萃取每個景點的特色描述，並寫入 SQL Server `ResortKnowledgeItem`：

```bash
python sync_knowledge_to_db.py
```

需先啟動 LM Studio 並載入對應模型（預設 `gemma-4-26b-a4b-it`）。

## 依賴套件

主要依賴（詳見 `requirements.txt`）：

- `langchain-core` / `langchain-community` / `langchain-openai` / `langchain-qdrant` / `langchain-text-splitters`
- `qdrant-client`
- `google-genai`
- `sqlalchemy` / `pyodbc`
- `pypdf`
- `python-dotenv`
