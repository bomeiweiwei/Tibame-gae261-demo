import os

from flask import Flask, render_template, request
from dotenv import load_dotenv

# Azure Translation
from azure.ai.translation.text import TextTranslationClient

from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError

# 載入 .env
load_dotenv()

text_translator = TextTranslationClient(
    credential=AzureKeyCredential(os.getenv("AZURE_TRANSLATOR_KEY")),
    endpoint=os.getenv("AZURE_TRANSLATOR_ENDPOINT"),
    region=os.getenv("AZURE_TRANSLATOR_REGION"),
)

app = Flask(__name__)

APP_NAME = os.getenv("APP_NAME", "Flask Azure Demo")
DEBUG = os.getenv("DEBUG", "True") == "True"


@app.route("/")
def home():
    return render_template("index.html", app_name=APP_NAME)


@app.route("/submit", methods=["POST"])
def submit():

    user_input = request.form.get("message")
    language = request.form.get("language")

    result = f"{azure_translate(user_input, language)}"

    return render_template(
        "index.html", result=result, user_input=user_input, app_name=APP_NAME
    )


def azure_translate(user_input, language):
    try:
        target_languages = [language]
        input_text_elements = [user_input]
        response = text_translator.translate(
            body=input_text_elements, to_language=target_languages
        )
        print(response)
        translation = response[0] if response else None
        if translation:
            result = ""
            for item in translation.translations:
                result += f"{item.to}: {item.text}\n"
            return result

    except HttpResponseError as exception:
        print(f"Error Code: {exception.error}")
    print(f"Message: {exception.error.message}")


if __name__ == "__main__":
    app.run(debug=DEBUG)
