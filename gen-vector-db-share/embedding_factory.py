import os
from typing import List

from dotenv import load_dotenv
from google import genai
from google.genai import types
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings

load_dotenv()


class GeminiEmbeddings(Embeddings):
    def __init__(self):
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

        if not credentials_path:
            raise ValueError("缺少 GOOGLE_APPLICATION_CREDENTIALS")

        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path

        self.client = genai.Client(
            vertexai=True,
            project=os.getenv("GOOGLE_CLOUD_PROJECT"),
            location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
        )

        self.model = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-2")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """將多個文檔（Documents）轉換為向量群（批次處理）"""
        if not texts:
            return []
        
        # 加上這行來觀察自動呼叫的行為
        print(f"--- LangChain 自動呼叫了 embed_documents，本次批次處理 {len(texts)} 筆文字 ---")
            
        # 修正：直接將整個 texts 列表傳入，利用 API 的批次處理功能
        result = self.client.models.embed_content(
            model=self.model,
            contents=texts,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT"  # 明確指定為文檔建立索引
            )
        )
        
        # 解析回傳的向量列表
        return [embedding.values for embedding in result.embeddings]

    def embed_query(self, text: str) -> List[float]:
        """將單一查詢（Query）轉換為向量"""
        result = self.client.models.embed_content(
            model=self.model,
            contents=text,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY"  # 明確指定為搜尋問題
            )
        )

        return result.embeddings[0].values


def get_embedding_function() -> Embeddings:
    provider = os.getenv("EMBEDDING_PROVIDER", "azure").lower()

    if provider == "azure":
        return OpenAIEmbeddings(
            model=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"),
            base_url=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        )

    if provider == "gemini":
        return GeminiEmbeddings()

    raise ValueError(
        f"不支援的 EMBEDDING_PROVIDER：{provider}，請使用 openai 或 gemini"
    )
