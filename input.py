import pandas as pd
import chromadb
from chromadb.utils import embedding_functions
from chromadb import HttpClient

# 步驟 1：連線到 VM 上的 ChromaDB
client = HttpClient(
    host="140.127.220.198",  
    port=8000
)

# 步驟 2：載入 CSV 檔案
df = pd.read_csv("food_additives.csv")  # 確保有 id、text、category 欄位

#清出Na值的問題
df = df.fillna("")


ids = df["項次"].astype(str).tolist()

# 製作 document：中文品名 + 英文品名 + 使用範圍
documents = [
    f"{row['中文品名']} ({row['英文品名']}): {row['使用食品範圍及限量']}"
    for _, row in df.iterrows()
]

# 將其他欄位放入 metadata
metadatas = [
    {
        "項次": row["項次"],
        "中文品名": row["中文品名"],
        "英文品名": row["英文品名"],
        "使用限制": row["使用限制"],
        "類別": row["類別"]
    }
    for _, row in df.iterrows()
]

client = chromadb.HttpClient(host="140.127.220.198", port=8000)  # ← 改成你的 VM IP
collection = client.get_or_create_collection(name="Food_Additives")

# 上傳資料
collection.add(ids=ids, documents=documents, metadatas=metadatas)

print("✅ 上傳完成！")

print("✅ 資料已成功寫入 ChromaDB！")