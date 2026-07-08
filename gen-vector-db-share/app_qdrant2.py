import json
import os
from dotenv import load_dotenv

from itinerary_knowledge_service import ItineraryKnowledgeService

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION_NAME = os.getenv(
    "QDRANT_COLLECTION_NAME",
    "resort_knowledge",
)


def validate_env():
    if not QDRANT_URL:
        raise ValueError("缺少 QDRANT_URL")

    if not QDRANT_API_KEY:
        raise ValueError("缺少 QDRANT_API_KEY")

    if not QDRANT_COLLECTION_NAME:
        raise ValueError("缺少 QDRANT_COLLECTION_NAME")


if __name__ == "__main__":

    validate_env()

    date_list = [
        "2026-05-31",
        "2026-06-01",
    ]

    service = ItineraryKnowledgeService()

    result = service.build_itinerary_by_dates(date_list)

    print(json.dumps(result, ensure_ascii=False, indent=2))
