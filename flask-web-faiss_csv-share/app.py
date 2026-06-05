import os

from flask import Flask, render_template, request
from dotenv import load_dotenv

# 載入 .env
load_dotenv()

app = Flask(__name__)

APP_NAME = os.getenv("APP_NAME", "Flask Azure Demo")
DEBUG = os.getenv("DEBUG", "True") == "True"

from langchain_community.vectorstores import FAISS

from langchain_huggingface import HuggingFaceEmbeddings

_embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
_vector_db = FAISS.load_local(
    "faiss_db", _embedding, allow_dangerous_deserialization=True
)

# from langchain_openai import OpenAIEmbeddings

# _embedding = OpenAIEmbeddings(
#     model=os.getenv("Azure_OpenAI_Embedding_DEPLOYMENT_NAME"),
#     base_url=os.getenv("Azure_OpenAI_ENDPOINT"),
#     api_key=os.getenv("Azure_OpenAI_KEY"),
# )
# _vector_db = FAISS.load_local(
#     "faiss_db2", _embedding, "index", allow_dangerous_deserialization=True
# )

def get_vector_db():
    return _vector_db


@app.route("/")
def home():
    return render_template("index.html", app_name=APP_NAME)


@app.route("/submit", methods=["POST"])
def submit():
    user_input = request.form.get("message")

    db = get_vector_db()
    results = db.similarity_search_with_score(user_input, k=3)
    """
    [
        (Document(...), score1),
        (Document(...), score2),
        (Document(...), score3)
    ]
    """
    for doc, score in results:
        print("=" * 50)
        print(f"Score: {score}")
        print(doc.page_content)
        print(doc.metadata)

    # 越小越相似
    # 找出分數最小的，取出第一個結果
    results.sort(key=lambda x: x[1])
    result = results[0][0].page_content

    return render_template(
        "index.html", result=result, user_input=user_input, app_name=APP_NAME
    )


if __name__ == "__main__":
    app.run(debug=DEBUG)
