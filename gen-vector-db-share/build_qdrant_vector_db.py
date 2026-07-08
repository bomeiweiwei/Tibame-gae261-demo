import os
import uuid
from pathlib import Path
from typing import Iterable, List

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from embedding_factory import get_embedding_function


load_dotenv()

PDF_DIR = Path(os.getenv("PDF_DIR", "knowledges"))

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "resort_knowledge")

QDRANT_BATCH_SIZE = int(os.getenv("QDRANT_BATCH_SIZE", "30"))
QDRANT_TIMEOUT_SECONDS = int(os.getenv("QDRANT_TIMEOUT_SECONDS", "180"))
QDRANT_FORCE_RECREATE = os.getenv("QDRANT_FORCE_RECREATE", "true").lower() == "true"


def parse_pdf_filename(pdf_path: Path) -> dict:
    """
    檔名格式：內部或外部-類別-景點名稱.pdf
    範例：外部-景點-傳統藝術中心.pdf
    """
    filename_without_ext = pdf_path.stem
    parts = filename_without_ext.split("-", maxsplit=2)

    if len(parts) != 3:
        return {
            "location_scope": "未分類",
            "category": "未分類",
            "place_name": filename_without_ext,
            "source_file": pdf_path.name,
        }

    return {
        "location_scope": parts[0],
        "category": parts[1],
        "place_name": parts[2],
        "source_file": pdf_path.name,
    }


def load_pdfs() -> List[Document]:
    documents: List[Document] = []

    for pdf_path in PDF_DIR.glob("*.pdf"):
        print(f"讀取 PDF：{pdf_path.name}")

        loader = PyPDFLoader(str(pdf_path))
        docs = loader.load()

        for doc in docs:
            doc.metadata.update(parse_pdf_filename(pdf_path))
            doc.metadata["source_path"] = str(pdf_path)

        documents.extend(docs)

    if not documents:
        raise FileNotFoundError(f"找不到任何 PDF：{PDF_DIR}")

    return documents


def split_documents(documents: List[Document]) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=80,
        separators=["\n\n", "\n", "。", "，", " ", ""],
    )

    chunks = splitter.split_documents(documents)

    for index, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = index

    return chunks


def batch_items(items: List[Document], batch_size: int) -> Iterable[List[Document]]:
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]


def validate_env() -> None:
    if not QDRANT_URL:
        raise ValueError("缺少 QDRANT_URL")

    if not QDRANT_API_KEY:
        raise ValueError("缺少 QDRANT_API_KEY")

    if QDRANT_BATCH_SIZE <= 0:
        raise ValueError("QDRANT_BATCH_SIZE 必須大於 0")


def build_point_id(doc: Document) -> str:
    source_file = doc.metadata.get("source_file", "unknown")
    page = doc.metadata.get("page", "unknown")
    chunk_index = doc.metadata.get("chunk_index", "unknown")
    raw_key = f"{source_file}:{page}:{chunk_index}:{doc.page_content}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, raw_key))


def create_or_recreate_collection(client: QdrantClient, vector_size: int) -> None:
    exists = client.collection_exists(QDRANT_COLLECTION_NAME)

    if exists and QDRANT_FORCE_RECREATE:
        print(f"刪除既有 Collection：{QDRANT_COLLECTION_NAME}")
        client.delete_collection(collection_name=QDRANT_COLLECTION_NAME)
        exists = False

    if not exists:
        print(f"建立 Collection：{QDRANT_COLLECTION_NAME}，vector_size={vector_size}")
        client.create_collection(
            collection_name=QDRANT_COLLECTION_NAME,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE,
            ),
        )
    else:
        print(f"使用既有 Collection：{QDRANT_COLLECTION_NAME}")


def main() -> None:
    validate_env()

    documents = load_pdfs()
    chunks = split_documents(documents)

    print(f"PDF 頁面數：{len(documents)}")
    print(f"Chunk 數量：{len(chunks)}")
    print(f"Qdrant Collection：{QDRANT_COLLECTION_NAME}")
    print(f"Batch Size：{QDRANT_BATCH_SIZE}")

    embedding_function = get_embedding_function()

    client = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        timeout=QDRANT_TIMEOUT_SECONDS,
    )

    collection_ready = False
    total_uploaded = 0

    for batch_index, batch in enumerate(batch_items(chunks, QDRANT_BATCH_SIZE), start=1):
        texts = [doc.page_content for doc in batch]

        print(f"產生第 {batch_index} 批 embedding，筆數：{len(batch)}")
        vectors = embedding_function.embed_documents(texts)

        if not vectors:
            continue

        if not collection_ready:
            vector_size = len(vectors[0])
            create_or_recreate_collection(client, vector_size)
            collection_ready = True

        points = []
        for doc, vector in zip(batch, vectors):
            payload = {
                "page_content": doc.page_content,
                "metadata": doc.metadata,
            }

            points.append(
                PointStruct(
                    id=build_point_id(doc),
                    vector=vector,
                    payload=payload,
                )
            )

        print(f"上傳第 {batch_index} 批到 Qdrant，筆數：{len(points)}")
        client.upsert(
            collection_name=QDRANT_COLLECTION_NAME,
            points=points,
            wait=True,
        )

        total_uploaded += len(points)
        print(f"目前已上傳：{total_uploaded}/{len(chunks)}")

    print("已成功將 PDF 向量資料上傳到 Qdrant Cloud")


if __name__ == "__main__":
    main()
