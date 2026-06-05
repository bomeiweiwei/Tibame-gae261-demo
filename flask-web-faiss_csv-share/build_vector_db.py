from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
import pandas as pd

animal_data = pd.read_csv("animal-fun-facts-dataset.csv")

animal_data["text"] = animal_data["text"].fillna("").astype(str)

embedding_function = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

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

faiss.save_local("faiss_db")

print("FAISS 建立完成")
