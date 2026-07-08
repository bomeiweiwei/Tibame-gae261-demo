import os
from dotenv import load_dotenv
from agent_framework.openai import OpenAIChatClient

from tools.traffic_tools import query_traffic

load_dotenv()

base_url = os.getenv("AZURE_OPENAI_ENDPOINT")
api_key = os.getenv("AZURE_OPENAI_API_KEY")
model = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")


traffic_agent = OpenAIChatClient(
    base_url=base_url,
    api_key=api_key,
    model=model,
).as_agent(
    instructions="""
    你是 traffic_agent。

    嚴格規則：
    - 你只能呼叫 traffic_tool。
    - 你只能回傳 traffic_tool 的結果。
    - 不可以自行補充交通方式。
    - 不可以自行推測路線、公車、火車、開車資訊。
    - 如果工具只回傳測試文字，你也只能回傳該測試文字。
    - 使用繁體中文回答。
    """,
    tools=[query_traffic],
)


async def run_traffic_agent(question: str) -> str:
    print(f"[traffic_agent] question: {question}")
    result = await traffic_agent.run(question)
    print(f"[traffic_agent] answer: {result.text}")
    return result.text