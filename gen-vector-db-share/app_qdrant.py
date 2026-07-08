import json
import os

from dotenv import load_dotenv

from rag_search_service import get_rag_search_service

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION_NAME = os.getenv(
    "QDRANT_COLLECTION_NAME",
    "resort_knowledge",
)

RAG_CATEGORIES = {
    "facility_hours",
    "attraction_hours",
    "facility_info",
    "rules",
    "price",
    "restaurant",
    "attraction",
    "room_facility",
    "room_service",
}

QA_CATEGORY_TO_RAG_CATEGORIES: dict[str, list[str] | None] = {
    "facility_hours": [
        "戶外設施",
        "室內設施",
    ],
    "attraction_hours": [
        "戶外旅遊景點",
        "室內旅遊景點",
        "戶外景點",
        "室內景點",
        "文化園區",
        "日式主題園區",
        "在地文化",
        "動物園",
        "博物館",
        "溫泉公園",
        "觀光園區",
        "觀光農場",
    ],
    "facility_info": [
        "戶外設施",
        "室內設施",
    ],
    "restaurant": [
        "餐飲美食",
    ],
    "attraction": [
        "戶外活動",
        "戶外旅遊景點",
        "戶外設施",
        "戶外景點",
        "文化園區",
        "日式主題園區",
        "在地文化",
        "室內活動",
        "室內旅遊景點",
        "室內設施",
        "室內景點",
        "動物園",
        "基礎介紹",
        "博物館",
        "溫泉公園",
        "觀光園區",
        "觀光農場",
    ],
    "rules": ["基礎介紹"],
    "price": ["基礎介紹"],
    "room_facility": ["基礎介紹"],
    "room_service": ["基礎介紹"],
}


def validate_env():
    if not QDRANT_URL:
        raise ValueError("缺少 QDRANT_URL")

    if not QDRANT_API_KEY:
        raise ValueError("缺少 QDRANT_API_KEY")

    if not QDRANT_COLLECTION_NAME:
        raise ValueError("缺少 QDRANT_COLLECTION_NAME")


if __name__ == "__main__":

    # 內/外部-catrgory-景點名稱.pdf
    print("=== 測試多個文件的catrgory ===")

    validate_env()

    service = get_rag_search_service()

    query = "冬山河適合親子去嗎？營業時間大概會開到幾點?"

    # 這邊要LLM幫你判定是哪個key，測試時自行決定你的key是屬於哪個
    qa_category = "attraction_hours"

    categories = QA_CATEGORY_TO_RAG_CATEGORIES.get(
        qa_category,
        None,
    )

    result = service.search_knowledge_by_categories(
        user_question=query,
        categories=categories,
        k=1,
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))

    print("=== 測試多個語句組成多個文件的catrgory ===")

    query = "冬山河適合親子去嗎？營業時間大概會開到幾點?附近有什麼餐廳好吃?"

    # 這邊要LLM幫你判定是哪個key，測試時自行決定你的key list是屬於哪個
    # key裡面的query是LLM幫你決定要帶什麼字去查，測試時自行決定文字內容
    qa_tasks = [
        {"category": "attraction", "query": "冬山河景點是否適合親子旅遊"},
        {"category": "attraction_hours", "query": "冬山河景點營業時間"},
        {"category": "restaurant", "query": "冬山河附近推薦的美食餐廳"},
    ]

    results = []
    for task in qa_tasks:
        categories = QA_CATEGORY_TO_RAG_CATEGORIES[task["category"]]
        result = service.search_knowledge_by_categories(
            user_question=task["query"],
            categories=categories,
            k=1,
        )
        results.append(result)
    print(json.dumps(results, ensure_ascii=False, indent=2))
