import os

from flask import Flask, render_template, request
from concurrent.futures import ThreadPoolExecutor

from enums.ai_type import AiType
from ai.factory import create_ai_langchain
from prompts.prompt_builder import build_prompt

from ai.azure_ask import Ask as AzureAsk
from ai.gemini_ask import Ask as GeminiAsk
from ai.ollama_ask import Ask as OllamaAsk
from ai.lmstudio_ask import Ask as LMStudioAsk

from ai.azure_ask import AskWithImage as AzureAskImage
from ai.gemini_ask import AskWithImage as GeminiAskImage
from ai.ollama_ask import AskWithImage as OllamaAskImage
from ai.lmstudio_ask import AskWithImage as LMStudioAskImage

from pathlib import Path

from core.config import get_settings

app = Flask(__name__)

settings = get_settings()

APP_NAME = settings.app_name
DEBUG = settings.debug


@app.route("/")
def home():
    active_tab = "tab1"
    image_url = os.path.join("static", "uploads", "images", "cat.png")
    return render_template("index.html", app_name=APP_NAME, image_url=image_url, active_tab=active_tab)


@app.route("/submit", methods=["POST"])
def submit():
    user_input = request.form.get("message")
    active_tab = request.form.get("active_tab", "tab1")

    providers = [
        AiType.GEMINI,
        AiType.AZURE,
        # AiType.OLLAMA,
        # AiType.LMSTUDIO,
    ]
    gemini_result, azure_result, ollama_result, lmstudio_result = ask_ai(
        providers, user_input
    )

    return render_template(
        "index.html",
        gemini_result=gemini_result,
        azure_result=azure_result,
        ollama_result=ollama_result,
        lmstudio_result=lmstudio_result,
        user_input=user_input,
        app_name=APP_NAME,
        active_tab=active_tab
    )

@app.route("/submit_with_img", methods=["POST"])
def submit_with_img():
    user_input = request.form.get("message")
    active_tab = request.form.get("active_tab", "tab2")

    providers = [
        AiType.GEMINI,
        AiType.AZURE,
        # AiType.OLLAMA,
        # AiType.LMSTUDIO,
    ]
    gemini_result, azure_result, ollama_result, lmstudio_result = ask_ai_image(
        providers, user_input
    )

    return render_template(
        "index.html",
        gemini_result=gemini_result,
        azure_result=azure_result,
        ollama_result=ollama_result,
        lmstudio_result=lmstudio_result,
        user_input=user_input,
        app_name=APP_NAME,
        active_tab=active_tab
    )


def ask_ai_with_text(ai_provider, ask_func, user_input):
    try:
        response = ask_func(user_input)
        return ai_provider, response
    except Exception as e:
        return ai_provider, f"發生錯誤：{e}"


def ask_ai_with_text_and_image(ai_provider, ask_func, user_input, image_url):
    try:
        response = ask_func(user_input, image_url)
        return ai_provider, response
    except Exception as e:
        return ai_provider, f"發生錯誤：{e}"


def ask_ai(providers: list, user_input: str):
    tasks = []

    if AiType.GEMINI in providers:
        tasks.append((AiType.GEMINI, GeminiAsk, user_input))
    if AiType.AZURE in providers:
        tasks.append((AiType.AZURE, AzureAsk, user_input))
    if AiType.OLLAMA in providers:
        tasks.append((AiType.OLLAMA, OllamaAsk, user_input))
    if AiType.LMSTUDIO in providers:
        tasks.append((AiType.LMSTUDIO, LMStudioAsk, user_input))

    with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
        results = list(executor.map(lambda task: ask_ai_with_text(*task), tasks))

    results_dict = {provider: result for provider, result in results}
    return (
        results_dict.get(AiType.GEMINI, "無回應"),
        results_dict.get(AiType.AZURE, "無回應"),
        results_dict.get(AiType.OLLAMA, "無回應"),
        results_dict.get(AiType.LMSTUDIO, "無回應"),
    )

def ask_ai_image(providers: list, user_input: str):
    tasks = []

    BASE_DIR = Path(__file__).resolve().parent

    image_path = BASE_DIR / "static" / "uploads" / "images" / "cat.png"
    # image_url = os.path.join("static", "uploads", "images", "cat.png")

    if AiType.GEMINI in providers:
        tasks.append((AiType.GEMINI, GeminiAskImage, user_input, image_path))
    if AiType.AZURE in providers:
        tasks.append((AiType.AZURE, AzureAskImage, user_input, image_path))
    if AiType.OLLAMA in providers:
        tasks.append((AiType.OLLAMA, OllamaAskImage, user_input, image_path))
    if AiType.LMSTUDIO in providers:
        tasks.append((AiType.LMSTUDIO, LMStudioAskImage, user_input, image_path))

    with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
        results = list(
            executor.map(lambda task: ask_ai_with_text_and_image(*task), tasks)
        )

    results_dict = {provider: result for provider, result in results}
    return (
        results_dict.get(AiType.GEMINI, "無回應"),
        results_dict.get(AiType.AZURE, "無回應"),
        results_dict.get(AiType.OLLAMA, "無回應"),
        results_dict.get(AiType.LMSTUDIO, "無回應"),
    )


if __name__ == "__main__":
    app.run(debug=DEBUG)
