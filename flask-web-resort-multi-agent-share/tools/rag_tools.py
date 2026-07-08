from typing import Annotated

from agent_framework import tool
from pydantic import Field


@tool(
    name="facility_hours_tool",
    description="測試用設施營業時間查詢工具，只回傳是否進入設施營業時間查詢流程。",
)
def query_facility_hours(
    question: Annotated[
        str,
        Field(description="設施營業時間問題，例如：游泳池開到幾點、健身房營業時間、設施維護時段"),
    ],
) -> dict:
    print(f"[RAG tool] 設施營業時間查詢：{question}")

    return {
        "status": "success",
        "report": f"已進入 RAG tool：設施營業時間查詢。問題：{question}。目前尚未串接真實 RAG 知識庫。"
    }


@tool(
    name="attraction_hours_tool",
    description="測試用景點營業時間查詢工具，只回傳是否進入景點營業時間查詢流程。",
)
def query_attraction_hours(
    question: Annotated[
        str,
        Field(description="景點營業時間問題，例如：冬山河開放時間、傳藝中心營業時間"),
    ],
) -> dict:
    print(f"[RAG tool] 景點營業時間查詢：{question}")

    return {
        "status": "success",
        "report": f"已進入 RAG tool：景點營業時間查詢。問題：{question}。目前尚未串接真實 RAG 知識庫。"
    }


@tool(
    name="rules_tool",
    description="測試用規範查詢工具，只回傳是否進入規範查詢流程。",
)
def query_rules(
    question: Annotated[
        str,
        Field(description="規範問題，例如：年齡限制、身高限制、服裝規定、人數限制、低消規定"),
    ],
) -> dict:
    print(f"[RAG tool] 規範查詢：{question}")

    return {
        "status": "success",
        "report": f"已進入 RAG tool：規範查詢。問題：{question}。目前尚未串接真實 RAG 知識庫。"
    }


@tool(
    name="restaurant_food_tool",
    description="測試用餐廳美食查詢工具，只回傳是否進入餐廳美食查詢流程。",
)
def query_restaurant_food(
    question: Annotated[
        str,
        Field(description="餐廳美食問題，例如：早餐供應時段、親子餐廳、素食餐廳、餐廳推薦"),
    ],
) -> dict:
    print(f"[RAG tool] 餐廳美食查詢：{question}")

    return {
        "status": "success",
        "report": f"已進入 RAG tool：餐廳美食查詢。問題：{question}。目前尚未串接真實 RAG 知識庫。"
    }