import os

from flask import Flask, render_template, request
from dotenv import load_dotenv

# Azure Translation
from azure.ai.translation.text import TextTranslationClient

# from azure.ai.translation.text.models import InputTextItem
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

    translation_result, language = azure_translate(user_input)
    transliterate_result = azure_transliterate(translation_result, language)

    result = f"{transliterate_result}"

    return render_template(
        "index.html", result=result, user_input=user_input, app_name=APP_NAME
    )


def azure_translate(user_input):

    try:
        target_languages = ["en", "zh-Hant", "ko", "ja"]
        input_text_elements = [user_input]

        response = text_translator.translate(
            body=input_text_elements, to_language=target_languages
        )
        print(response)
        translation = response[0] if response else None

        if translation:
            detected_language = translation.detected_language.language
            if detected_language == "zh-Hant" or detected_language == "zh-Hans":
                detected_language = "zh-Hant"

            index = target_languages.index(detected_language)
            return (
                    translation.translations[index].text,
                    target_languages[index],
                )

    except HttpResponseError as exception:
        print(f"Error Code: {exception.error}")
        print(f"Message: {exception.error.message}")


# 用拉丁文教我怎麼唸
def azure_transliterate(user_input, language):
    try:
        if language == "en":
            return user_input
        # language = "zh-Hans"
        if language == "zh-Hant":
            from_script = "Hant"
        elif language == "ko":
            from_script = "Kore"
        elif language == "ja":
            from_script = "Jpan"
            
        # from_script = "Hans"
        to_script = "Latn"
        input_text_elements = [user_input]

        response = text_translator.transliterate(
            body=input_text_elements,
            language=language,
            from_script=from_script,
            to_script=to_script,
        )
        transliteration = response[0] if response else None

        if transliteration:
            print(
                f"Input text was transliterated to '{transliteration.script}' script. Transliterated text: '{transliteration.text}'."
            )
            return transliteration.text

    except HttpResponseError as exception:
        if exception.error is not None:
            print(f"Error Code: {exception.error.code}")
            print(f"Message: {exception.error.message}")
        raise


if __name__ == "__main__":
    app.run(debug=DEBUG)
