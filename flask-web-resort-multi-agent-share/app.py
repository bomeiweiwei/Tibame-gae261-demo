import os
import asyncio

from flask import Flask, render_template, request
from dotenv import load_dotenv

# from agents.main_agent_service import route_question
from agents.main_agent_tool_service import route_question

load_dotenv()

app = Flask(__name__)

APP_NAME = os.getenv("APP_NAME", "Flask Azure 測試網站")
DEBUG = os.getenv("DEBUG", "True") == "True"


@app.route("/")
def home():
    return render_template("index.html", app_name=APP_NAME)


@app.route("/submit", methods=["POST"])
def submit():
    user_input = request.form.get("message", "").strip()

    result = asyncio.run(route_question(user_input))

    return render_template(
        "index.html", result=result, user_input=user_input, app_name=APP_NAME
    )


if __name__ == "__main__":
    app.run(debug=DEBUG)
