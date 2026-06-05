import os

from flask import Flask, render_template, request, Response, jsonify
from dotenv import load_dotenv

from lab_speech_to_text import speech_to_text
from lab_azure_translate import azure_translate
from lab_azure_transliterate import azure_transliterate
from lab_azure_speech import azure_speech

# 載入 .env
load_dotenv()

UPLOAD_FOLDER = "static"

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

APP_NAME = os.getenv("APP_NAME", "Flask Azure Demo")
DEBUG = os.getenv("DEBUG", "True") == "True"



@app.route("/")
def home():
    return render_template("index.html", app_name=APP_NAME)


@app.route("/submit", methods=["POST"])
def submit():

    user_input = request.form.get("message")

    translation_result, language, zh_trans = azure_translate(user_input)
    print("zh_trans", zh_trans)
    transliterate_result = azure_transliterate(translation_result, language)

    result = f"{transliterate_result}"

    # audio = azure_speech(translation_result)

    return render_template(
        "index.html",
        result=result,
        user_input=translation_result,
        language=language,
        app_name=APP_NAME,
        zh_trans=zh_trans,
    )


@app.route("/stt", methods=["POST"])
def stt():
    audio_file = request.files.get("audio")
    if not audio_file:
        return jsonify({"error": "No audio"}), 400

    text = speech_to_text(audio_file)
    if text is None:
        return jsonify({"error": "Recognition failed"}), 500

    return jsonify({"text": text})


@app.route("/speak")
def speak():

    text = request.args.get("text", "")
    language = request.args.get("language", "en")

    if not text:
        return "No text", 400

    audio_bytes = azure_speech(text, language)

    if not audio_bytes:
        return "Speech synthesis failed", 500

    return Response(audio_bytes, mimetype="audio/mpeg")





if __name__ == "__main__":
    app.run(debug=DEBUG)
