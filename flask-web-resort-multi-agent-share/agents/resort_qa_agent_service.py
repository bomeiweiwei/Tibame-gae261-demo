import os
from dotenv import load_dotenv
from agent_framework.openai import OpenAIChatClient

from tools.rag_tools import (
    query_facility_hours,
    query_attraction_hours,
    query_rules,
    query_restaurant_food,
)

load_dotenv()

base_url = os.getenv("AZURE_OPENAI_ENDPOINT")
api_key = os.getenv("AZURE_OPENAI_API_KEY")
model = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")


resort_qa_agent = OpenAIChatClient(
    base_url=base_url,
    api_key=api_key,
    model=model,
).as_agent(
    name="ResortQAAgent",
    instructions="""
你是 resort_qa_agent。

你的任務：
判斷使用者問題屬於哪一種渡假村 QA 類別，並呼叫正確的 RAG tool。

可用工具：
- facility_hours_tool：設施營業時間、清潔維護時段
- attraction_hours_tool：景點營業時間、開放時間
- rules_tool：使用規範、年齡限制、身高限制、服裝規定、人數限制、低消
- restaurant_food_tool：早餐、餐廳、美食、親子用餐、素食餐廳

嚴格規則：
- 你只能呼叫上述 RAG tools。
- 你只能回傳 RAG tool 的結果。
- 不可以自行回答設施營業時間。
- 不可以自行回答景點開放時間。
- 不可以自行回答使用規範。
- 不可以自行回答餐廳、美食、早餐或素食推薦。
- 不可以根據常識、推測、記憶或一般飯店經驗補充答案。
- 如果工具只回傳測試文字，你也只能回傳該測試文字。
- 如果問題同時包含多個類別，可以呼叫多個 tool。
- 使用繁體中文回答。
""",
    tools=[
        query_facility_hours,
        query_attraction_hours,
        query_rules,
        query_restaurant_food,
    ],
)