import os

from flask import Flask, render_template, request
from dotenv import load_dotenv

# Azure Text Analytics
from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import TextAnalyticsClient

# 載入 .env
load_dotenv()

# 初始化 Azure Text Analytics 客戶端
text_analytics_credential = AzureKeyCredential(os.getenv("AZURE_TEXTANALYTICS_KEY"))
text_analytics_endpoint = os.getenv("AZURE_TEXTANALYTICS_ENDPOINT")
text_analytics_client = TextAnalyticsClient(
    endpoint=text_analytics_endpoint,
    credential=text_analytics_credential,
    default_language="zh", # default_language 與你輸入的語系相同可抓主詞
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

    result = f"{azure_sentiment(user_input)}"

    return render_template(
        "index.html", result=result, user_input=user_input, app_name=APP_NAME
    )

def azure_sentiment(user_input):
    documents = [user_input]
    response = text_analytics_client.analyze_sentiment(
        documents, 
        show_opinion_mining=True)
    print("="*50)
    print(response)
    docs = [doc for doc in response if not doc.is_error]
    for idx, doc in enumerate(docs):
        print(f"Document text : {documents[idx]}")
        print(f"Overall sentiment : {doc.sentiment}")
    print("="*50)
    sentiment_dict = {
        "positive": "正面",
        "neutral": "中立",
        "negative": "負面",
        "mixed": "混合"
    }

    if sentiment_dict[docs[0].sentiment] == "mixed":
        return f"{sentiment_dict[docs[0].sentiment]}。"
    else:
        return f"{sentiment_dict[docs[0].sentiment]}。分數：{docs[0].confidence_scores[docs[0].sentiment]}"


if __name__ == "__main__":
    app.run(debug=DEBUG)
