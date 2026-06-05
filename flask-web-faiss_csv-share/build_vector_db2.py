from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
import pandas as pd
import os

from dotenv import load_dotenv
load_dotenv()

os.environ["KMP_DUPLICATE_LIB_OK"] = "True"

animal_data = pd.read_csv("animal-fun-facts-dataset.csv")

embedding_function = OpenAIEmbeddings(
    model=os.getenv("Azure_OpenAI_Embedding_DEPLOYMENT_NAME"),
    base_url=os.getenv("Azure_OpenAI_ENDPOINT"),
    api_key=os.getenv("Azure_OpenAI_KEY"),
)

animal_data["text"] = animal_data["text"].fillna("").astype(str)

metadatas = []

for _, row in animal_data.iterrows():
    metadatas.append(
        {
            "Animal Name": row["animal_name"],
            "Source URL": row["source"],
        }
    )

faiss = FAISS.from_texts(
    animal_data["text"].tolist(),
    embedding_function,
    metadatas=metadatas,
)

faiss.save_local("faiss_db2")

print("FAISS 建立完成")
