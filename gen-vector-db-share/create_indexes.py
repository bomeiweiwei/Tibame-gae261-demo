import os
from qdrant_client import QdrantClient
from dotenv import load_dotenv
from qdrant_client.models import PayloadSchemaType

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION_NAME = os.getenv(
    "QDRANT_COLLECTION_NAME",
    "resort_knowledge",
)

def validate_env() -> None:
    if not QDRANT_URL:
        raise ValueError("缺少 QDRANT_URL")

    if not QDRANT_API_KEY:
        raise ValueError("缺少 QDRANT_API_KEY")

def create_payload_indexes():
    """
    Qdrant Cloud 如果 collection 啟用了需要 payload index 的查詢模式，
    使用 filter 前必須先替要查詢的 payload 欄位建立 index。

    目前行程推薦會用 category 過濾：
    metadata.category == 餐飲美食

    另外順手建立幾個常用 metadata index，之後查詢會比較穩。
    """
    validate_env()
    
    client = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        timeout=120,
    )

    index_fields = [
        "metadata.category",
        "metadata.location_scope",
        "metadata.place_name",
        "metadata.source_file",
    ]

    for field_name in index_fields:
        try:
            client.create_payload_index(
                collection_name=QDRANT_COLLECTION_NAME,
                field_name=field_name,
                field_schema=PayloadSchemaType.KEYWORD,
            )
            print(f"已建立 Qdrant payload index：{field_name}")
        except Exception as ex:
            message = str(ex)

            # index 已存在時忽略，不中斷主程式
            if "already exists" in message.lower() or "existing" in message.lower():
                print(f"Qdrant payload index 已存在：{field_name}")
                continue

            print(f"建立 Qdrant payload index 失敗：{field_name}")
            print(message)
            raise

if __name__ == "__main__":
    create_payload_indexes()