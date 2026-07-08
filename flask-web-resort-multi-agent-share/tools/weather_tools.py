from typing import Annotated
from pydantic import Field
from agent_framework import tool
import requests
import os


@tool(name="weather_tool", description="Retrieves weather information for any city.")
def get_weather(
    city: Annotated[
        str, Field(description="The city to get the weather for. MUST be in English.")
    ],
) -> dict:
    """Get the weather for a given city."""

    print(f"[Function call] get_weather with city: {city}")

    api_key = os.getenv("OPEN_WEATHER_MAP_API_KEY")

    if not api_key:
        return {
            "status": "error",
            "error_message": "OpenWeatherMap API key is not set.",
        }

    url = (
        "http://api.openweathermap.org/data/2.5/weather"
        f"?q={city}&appid={api_key}&units=metric"
    )

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()

        weather_description = data["weather"][0]["description"]
        temperature = data["main"]["temp"]

        report = (
            f"The weather in {city} is {weather_description}, "
            f"temperature is {temperature}°C."
        )

        print(f"[Function response] {report}")

        return {"status": "success", "report": report}

    except requests.exceptions.RequestException as e:
        return {"status": "error", "error_message": f"Weather API error: {str(e)}"}
