import os

from langchain_qdrant import QdrantVectorStore

from embedding_factory import get_embedding_function
from dotenv import load_dotenv
import pyodbc
from qdrant_client.models import FieldCondition, Filter, MatchAny

load_dotenv()


class ItineraryKnowledgeService:
    def __init__(self):
        self._validate_env()
        self.vector_db = self._load_vector_db()

    def _validate_env(self):
        if not os.getenv("QDRANT_URL"):
            raise ValueError("缺少 QDRANT_URL")

        if not os.getenv("QDRANT_API_KEY"):
            raise ValueError("缺少 QDRANT_API_KEY")

        if not os.getenv("QDRANT_COLLECTION_NAME"):
            raise ValueError("缺少 QDRANT_COLLECTION_NAME")

    def _load_vector_db(self) -> QdrantVectorStore:
        embedding_function = get_embedding_function()

        return QdrantVectorStore.from_existing_collection(
            embedding=embedding_function,
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY"),
            collection_name=os.getenv("QDRANT_COLLECTION_NAME"),
        )

    def get_db_connection(self):
        conn_str = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            f"SERVER={os.getenv('DB_SERVER')};"
            f"DATABASE={os.getenv('DB_NAME')};"
            f"UID={os.getenv('DB_USER')};"
            f"PWD={os.getenv('DB_PASSWORD')};"
            "TrustServerCertificate=yes;"
        )

        return pyodbc.connect(conn_str)

    def build_itinerary_by_dates(
        self,
        date_list: list[str],
    ) -> list[dict]:
        conn = self.get_db_connection()
        try:
            itinerary_list = []
            search_plans = self._get_search_plans()

            for date in date_list:
                used_places = set()
                daily_schedules = []

                for plan in search_plans:
                    results = self.vector_db.similarity_search_with_score(
                        query=plan["query"],
                        k=20,
                        filter=self._build_category_filter(plan["categories"]),
                    )

                    selected_items = []

                    for doc, score in results:
                        place_name = doc.metadata.get("place_name")
                        source_file = doc.metadata.get("source_file")

                        if not place_name or not source_file:
                            continue

                        # 同一天不要重複景點
                        if place_name in used_places:
                            continue

                        db_item = self._get_knowledge_item_by_source_file(
                            conn=conn,
                            source_file=source_file,
                        )

                        if db_item is None:
                            continue

                        feature = db_item["feature"] or ""
                        selected_items.append(
                            {
                                "title": db_item["place_name"],
                                "content": feature[:30],
                                "preference": db_item["category"],
                                # "score": float(score),
                            }
                        )

                        used_places.add(place_name)

                        if len(selected_items) >= plan["k"]:
                            break

                    daily_schedules.append(
                        {
                            "time": plan["time"],
                            "recommendations": selected_items,
                        }
                    )

                itinerary_list.append(
                    {
                        "date": date,
                        "schedules": daily_schedules,
                    }
                )
        finally:
            conn.close()

        return itinerary_list

    def _build_category_filter(
        self,
        categories: list[str] | None,
    ) -> Filter | None:
        if not categories:
            return None

        return Filter(
            must=[
                FieldCondition(
                    key="metadata.category",
                    match=MatchAny(any=categories),
                )
            ]
        )

    def _get_search_plans(self) -> list[dict]:
        return [
            {
                "time": "09:00",
                "query": "適合早上開始的餐廳或早餐推薦，適合VIP客戶，交通方便",
                "categories": ["餐廳美食"],
                "k": 1,
            },
            {
                "time": "11:00",
                "query": "適合上午安排的渡假村內外景點，行程不要太累，適合親子或家庭",
                "categories": None,
                "k": 2,
            },
            {
                "time": "13:00",
                "query": "適合午餐後安排的景點或室內活動，適合下午時段",
                "categories": None,
                "k": 2,
            },
            {
                "time": "15:00",
                "query": "適合下午茶、輕鬆散步、文化體驗或親子活動的景點",
                "categories": None,
                "k": 2,
            },
            {
                "time": "18:00",
                "query": "適合晚上用餐的餐廳推薦，適合VIP客戶與家庭旅客",
                "categories": ["餐廳美食"],
                "k": 1,
            },
        ]

    def _get_knowledge_item_by_source_file(
        self,
        conn,
        source_file: str,
    ) -> dict | None:
        cursor = conn.cursor()

        sql = """
            SELECT
                PlaceName,
                Category,
                Feature
            FROM ResortKnowledgeItem
            WHERE SourceFile = ?
            AND IsActive = 1
        """

        cursor.execute(sql, source_file)
        row = cursor.fetchone()

        if row is None:
            return None

        return {
            "place_name": row.PlaceName,
            "category": row.Category,
            "feature": row.Feature,
        }
