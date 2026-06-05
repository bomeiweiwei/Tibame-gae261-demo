import os

from flask import Flask, render_template, request
from dotenv import load_dotenv

# 載入 .env
load_dotenv()

app = Flask(__name__)

APP_NAME = os.getenv("APP_NAME", "Flask Azure Demo")
DEBUG = os.getenv("DEBUG", "True") == "True"


@app.route("/")
def home():
    return render_template(
        "index.html",
        app_name=APP_NAME
    )


@app.route("/submit", methods=["POST"])
def submit():

    user_input = request.form.get("message")

    result = f"你輸入的是：{user_input}"

    return render_template(
        "index.html",
        result=result,
        user_input=user_input,
        app_name=APP_NAME
    )


if __name__ == "__main__":
    app.run(debug=DEBUG)