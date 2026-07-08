import os
from dotenv import load_dotenv
from agent_framework.openai import OpenAIChatClient

from tools.weather_tools import get_weather

load_dotenv()


base_url = os.getenv("AZURE_OPENAI_ENDPOINT")
api_key = os.getenv("AZURE_OPENAI_API_KEY")
model = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")


weather_agent = OpenAIChatClient(
    base_url=base_url,
    api_key=api_key,
    model=model,
).as_agent(
    instructions="""
    You are a weather assistant.
    You can only answer weather-related information.
    Do not answer traffic, route planning, restaurant, attraction, or resort policy questions.
    When calling the weather_tool, city name must be in English.
    使用繁體中文回答問題。
    """,
    tools=[get_weather],
)


async def run_weather_agent(question: str) -> str:
    print(f"[weather_agent] question: {question}")

    result = await weather_agent.run(question)

    print(f"[weather_agent] answer: {result.text}")

    return result.text