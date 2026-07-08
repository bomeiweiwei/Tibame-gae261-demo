import os
from pathlib import Path

import pyodbc
from dotenv import load_dotenv
from pypdf import PdfReader
from langchain_openai import ChatOpenAI


load_dotenv()

PDF_DIR = Path(os.getenv("PDF_DIR", "knowledges"))


def parse_pdf_filename(pdf_path: Path) -> dict:
    filename_without_ext = pdf_path.stem
    parts = filename_without_ext.split("-", maxsplit=2)

    if len(parts) != 3:
        return {
            "location_scope": "未分類",
            "category": "未分類",
            "place_name": filename_without_ext,
            "source_file": pdf_path.name,
            "source_path": str(pdf_path),
        }

    return {
        "location_scope": parts[0],
        "category": parts[1],
        "place_name": parts[2],
        "source_file": pdf_path.name,
        "source_path": str(pdf_path),
    }


def extract_pdf_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    texts = []

    for page in reader.pages:
        text = page.extract_text() or ""
        texts.append(text.strip())

    return "\n\n".join(texts).strip()


def get_db_connection():
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")

    conn_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={user};"
        f"PWD={password};"
        "TrustServerCertificate=yes;"
    )

    return pyodbc.connect(conn_str)


def create_llm():
    provider = os.getenv("LLM_PROVIDER", "lmstudio").lower()

    if provider == "lmstudio":
        return ChatOpenAI(
            model=os.getenv("LMSTUDIO_MODEL_NAME", "gemma-4-26b-a4b-it"),
            base_url=os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1"),
            api_key=os.getenv("LMSTUDIO_API_KEY", "lm-studio"),
            temperature=0.2,
        )

    raise ValueError(f"不支援的 LLM_PROVIDER：{provider}")


def generate_feature(llm, place_name: str, category: str, full_content: str) -> str:
    prompt = f"""
你是渡假村行程推薦系統的資料整理助手。

請根據以下景點資料，萃取「景點特色」，並簡單敘述。

輸出規則：
- 使用繁體中文
- 最多30 字
- 適合放在前端行程推薦卡片
- 不要條列式
- 不要 Markdown
- 不要加入原文沒有的資訊
- 聚焦於特色、體驗亮點、適合族群、交通便利性

景點名稱：{place_name}
類別：{category}

原始資料：
{full_content[:4000]}
"""

    response = llm.invoke(prompt)
    return response.content.strip()


def upsert_knowledge_item(conn, item: dict):
    sql = """
    MERGE ResortKnowledgeItem AS target
    USING (
        SELECT
            ? AS SourceFile
    ) AS source
    ON target.SourceFile = source.SourceFile

    WHEN MATCHED THEN
        UPDATE SET
            LocationScope = ?,
            Category = ?,
            PlaceName = ?,
            SourcePath = ?,
            FullContent = ?,
            Feature = ?,
            UpdatedAt = SYSDATETIME()

    WHEN NOT MATCHED THEN
        INSERT (
            LocationScope,
            Category,
            PlaceName,
            SourceFile,
            SourcePath,
            FullContent,
            Feature
        )
        VALUES (?, ?, ?, ?, ?, ?, ?);
    """

    cursor = conn.cursor()
    cursor.execute(
        sql,
        item["source_file"],

        item["location_scope"],
        item["category"],
        item["place_name"],
        item["source_path"],
        item["full_content"],
        item["feature"],

        item["location_scope"],
        item["category"],
        item["place_name"],
        item["source_file"],
        item["source_path"],
        item["full_content"],
        item["feature"],
    )
    conn.commit()


def sync_all_pdfs():
    pdf_files = list(PDF_DIR.glob("*.pdf"))

    if not pdf_files:
        raise FileNotFoundError(f"找不到 PDF 檔案：{PDF_DIR}")

    conn = get_db_connection()
    llm = create_llm()

    for pdf_path in pdf_files:
        print("=" * 80)
        print(f"處理檔案：{pdf_path.name}")

        item = parse_pdf_filename(pdf_path)
        full_content = extract_pdf_text(pdf_path)

        if not full_content:
            print("PDF 無法擷取文字，略過")
            continue

        feature = generate_feature(
            llm=llm,
            place_name=item["place_name"],
            category=item["category"],
            full_content=full_content,
        )

        item["full_content"] = full_content
        item["feature"] = feature

        upsert_knowledge_item(conn, item)

        print(f"已寫入資料庫：{item['place_name']}")
        print(f"Feature：{feature}")

    conn.close()


if __name__ == "__main__":
    sync_all_pdfs()