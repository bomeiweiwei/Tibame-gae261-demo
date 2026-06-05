import os

from flask import Flask, render_template, request
from dotenv import load_dotenv

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import FAISS

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

app = Flask(__name__)

APP_NAME = os.getenv("APP_NAME", "Flask RAG Demo")
DEBUG = os.getenv("DEBUG", "True") == "True"

TEXT_PATH = "state_of_the_union.txt"
FAISS_INDEX_PATH = "faiss_index"


def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )


def build_vector_db():
    embeddings = get_embeddings()

    loader = TextLoader(
        TEXT_PATH,
        autodetect_encoding=True,
        encoding="utf-8",
    )

    documents = loader.load()

    text_splitter = CharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
    )

    docs = text_splitter.split_documents(documents)

    db = FAISS.from_documents(docs, embeddings)
    db.save_local(FAISS_INDEX_PATH)

    return db


def load_vector_db():
    embeddings = get_embeddings()

    if os.path.exists(FAISS_INDEX_PATH):
        return FAISS.load_local(
            FAISS_INDEX_PATH,
            embeddings,
            allow_dangerous_deserialization=True,
        )

    return build_vector_db()


db = load_vector_db()


def get_vector_db():
    return db


@app.route("/")
def home():
    return render_template("index.html", app_name=APP_NAME)


@app.route("/submit", methods=["POST"])
def submit():
    user_input = request.form.get("message", "")

    db = get_vector_db()
    results = db.similarity_search_with_score(user_input, k=3)

    context = "\n\n".join(
        [
            f"文件片段 {i + 1}：\n{doc.page_content}\n相似度分數：{score}"
            for i, (doc, score) in enumerate(results)
        ]
    )

    result = get_answer_by_google(user_input, context)

    return render_template(
        "index.html",
        result=result,
        user_input=user_input,
        app_name=APP_NAME,
    )


def get_answer_by_google(question, context):
    llm_gemini = ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash"),
        google_api_key=os.getenv("GEMINI_API_KEY"),
    )

    prompt = ChatPromptTemplate.from_template(
        """
請只根據下方提供的文件內容回答問題。
如果文件內容找不到答案，請回答：「根據目前提供的文件內容，找不到明確答案。」

<context>
{context}
</context>

使用者問題：
{input}
"""
    )

    output_parser = StrOutputParser()
    chain = prompt | llm_gemini | output_parser

    return chain.invoke(
        {
            "input": question,
            "context": context,
        }
    ).strip()


if __name__ == "__main__":
    app.run(debug=DEBUG)