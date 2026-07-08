from typing import Annotated
from pydantic import Field
from agent_framework import tool


@tool(
    name="traffic_tool",
    description="測試用交通查詢工具，只回傳是否進入交通查詢流程。"
)
def query_traffic(
    destination: Annotated[
        str,
        Field(description="目的地，例如：冬山河、傳藝中心、羅東夜市")
    ],
) -> dict:
    print(f"[Traffic API tool] 交通查詢：{destination}")

    return {
        "status": "success",
        "report": f"已進入 Traffic API tool：交通查詢，目的地：{destination}。目前尚未串接真實交通 API。"
    }