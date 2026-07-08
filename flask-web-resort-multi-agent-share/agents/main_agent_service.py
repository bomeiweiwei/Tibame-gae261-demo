from agents.resort_qa_agent_service import run_resort_qa_agent
from agents.weather_agent_service import run_weather_agent
from agents.traffic_agent_service import run_traffic_agent


def is_weather_question(question: str) -> bool:
    return any(keyword in question for keyword in [
        "天氣", "下雨", "氣溫", "帶傘", "雨", "颱風", "晴天", "陰天"
    ])


def is_traffic_question(question: str) -> bool:
    return any(keyword in question for keyword in [
        "交通", "塞車", "路況", "怎麼去", "如何到達", "開車", "公車", "火車", "路線"
    ])


def is_resort_qa_question(question: str) -> bool:
    return any(keyword in question for keyword in [
        "游泳池", "健身房", "設施", "營業時間", "幾點開", "幾點關",
        "景點", "冬山河", "傳藝", "規範", "規定", "禁止",
        "餐廳", "早餐", "晚餐", "美食", "吃"
    ])


def extract_place(question: str) -> str:
    if "冬山河" in question:
        return "冬山河"
    if "傳藝" in question:
        return "國立傳統藝術中心"
    return "目的地"


async def route_question(question: str) -> str:
    print(f"[main_agent] 收到問題：{question}")

    results = []
    place = extract_place(question)

    if is_resort_qa_question(question):
        print("[main_agent] routing -> resort_qa_agent")
        resort_question = f"請查詢{place}的景點資訊或營業時間。"
        resort_result = run_resort_qa_agent(resort_question)
        results.append(f"【渡假村知識庫】\n{resort_result}")

    if is_weather_question(question):
        print("[main_agent] routing -> weather_agent")
        weather_question = f"請查詢{place}附近目前天氣，只回答天氣、氣溫、降雨與出遊建議，不要回答交通。"
        weather_result = await run_weather_agent(weather_question)
        results.append(f"【天氣查詢】\n{weather_result}")

    if is_traffic_question(question):
        print("[main_agent] routing -> traffic_agent")
        traffic_question = f"請查詢從渡假村到{place}的交通方式。"
        traffic_result = run_traffic_agent(traffic_question)
        results.append(f"【交通查詢】\n{traffic_result}")

    if not results:
        return "抱歉，目前僅提供渡假村相關服務資訊。"

    return "\n\n".join(results)