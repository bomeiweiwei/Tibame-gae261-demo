import os
from dotenv import load_dotenv
from agent_framework.openai import OpenAIChatClient

from agents.weather_agent_service import weather_agent
from agents.traffic_agent_service import traffic_agent
from agents.resort_qa_agent_service import resort_qa_agent

load_dotenv()

base_url = os.getenv("AZURE_OPENAI_ENDPOINT")
api_key = os.getenv("AZURE_OPENAI_API_KEY")
model = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")


weather_tool = weather_agent.as_tool(
    name="WeatherLookup",
    description="""
    查詢指定地點的即時天氣、氣溫、降雨狀況與出遊天氣建議。
    只處理天氣問題，不處理交通、路線、景點介紹。
    """,
    arg_name="query",
    arg_description="使用者想查詢天氣的地點或天氣問題。",
)


traffic_tool = traffic_agent.as_tool(
    name="TrafficLookup",
    description="""
    必須用於所有交通、路線、怎麼去、如何到達、塞車、開車、公車、火車問題。
    查詢從渡假村或指定出發地到目的地的交通方式。
    main_agent 不可以自行回答交通問題，必須呼叫此工具。
    """,
    arg_name="query",
    arg_description="交通查詢問題，例如：從渡假村到冬山河怎麼去。",
)

resort_qa_tool = resort_qa_agent.as_tool(
    name="ResortQALookup",
    description="""
查詢渡假村知識庫 QA。

適用範圍：
- 設施營業時間查詢
- 景點營業時間查詢
- 規範查詢
- 餐廳美食查詢

嚴格限制：
main_agent 遇到上述問題時，必須呼叫此工具。
main_agent 不可以自行回答營業時間、開放時間、規範、餐廳、美食、早餐、低消、人數限制、年齡限制、身高限制、服裝規定。
如果此工具只回傳測試文字，main_agent 也只能回傳該測試文字。
""",
    arg_name="query",
    arg_description="使用者的渡假村 QA 問題。",
)


main_agent = OpenAIChatClient(
    base_url=base_url,
    api_key=api_key,
    model=model,
).as_agent(
    instructions="""
你是渡假村智慧客服的 main_agent。

你的任務：
1. 分析使用者問題
2. 呼叫正確工具
3. 整合工具回傳結果

可用工具：
- WeatherLookup：天氣查詢
- TrafficLookup：交通查詢
- ResortQALookup：渡假村 QA、設施、景點、規範、餐廳美食查詢

嚴格規則：
- 遇到天氣問題，必須呼叫 WeatherLookup。
- 遇到交通問題，必須呼叫 TrafficLookup。
- 遇到渡假村 QA、設施、景點、規範、餐廳、美食問題，必須呼叫 ResortQALookup。
- 如果問題同時包含天氣與交通，兩個工具都必須呼叫。
- 如果問題同時包含多種類型，可以呼叫多個工具。
- 你只能根據工具回傳內容回答。
- 不可以自行補充工具沒有提供的資料。
- 不可以自行推測交通、天氣、營業時間、規範或餐廳資訊。
- 如果工具回傳「尚未串接真實 API」，你必須如實告知。
- 使用繁體中文回答。
""",
    tools=[
        weather_tool,
        traffic_tool,
        resort_qa_tool,
    ],
)


async def route_question(question: str) -> str:
    print(f"[main_agent_tool] 收到問題：{question}")

    result = await main_agent.run(question)

    print(f"[main_agent_tool] 回答：{result.text}")

    return result.text
