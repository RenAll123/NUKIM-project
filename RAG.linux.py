import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from flask import Flask, request, jsonify
import requests
import uuid
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
# 初始化嵌入模型
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# 初始化 Chroma（儲存在本地資料夾 ./chroma_db）
chroma_client = chromadb.PersistentClient(path="./chroma")
collection = chroma_client.get_or_create_collection(name="Food_Additives")

# 載入資料並建檔（只需執行一次）
#def load_documents():
    #with open("docs.txt", "r", encoding="utf-8") as f:
        #lines = [line.strip() for line in f if line.strip()]
    #ids = [str(uuid.uuid4()) for _ in lines]
    #embeddings = embedding_model.encode(lines).tolist()
    #collection.add(documents=lines, embeddings=embeddings, ids=ids)
    #chroma_client.persist()  # 儲存到本地資料夾

# 啟用這行只在首次建立資料庫時執行
#load_documents()
#print("目前資料庫中有的 collections:", chroma_client.list_collections())

def extract_possible_names():
    possible_names = set()
    all = collection.get(include=["metadatas"])  # 調整 limit 如需要

    for meta in all["metadatas"]:
        if meta is None:
            continue
        if "中文品名" in meta:
            possible_names.add(meta["中文品名"])
        if "英文品名" in meta:
            possible_names.add(meta["英文品名"])

    return list(possible_names)

possible_names = extract_possible_names()

# 根據輸入查找是否包含已知品名
def find_name_in_query(user_input, name_list):
    for name in name_list:
        if name and name in user_input:
            return name
    return None

# 查詢 Chroma
def search_documents(query, top_k=10):
    query_embedding = embedding_model.encode(query).tolist()

    # 嘗試加入 keyword filter
    matched_docs = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where_document={"$contains": query}  # 原始文字中包含 query 字詞
    )

    # 若字面搜尋找不到，再退回純向量比對
    if len(matched_docs["documents"][0]) == 0:
            matched_docs = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
    )

    return matched_docs["documents"][0], matched_docs["metadatas"][0]


# 呼叫本地 Ollama
def ask_ollama(prompt, model="foodsafety-bot:latest"):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False
        }
    )
    return response.json()['response']
# 建構提示詞
def build_prompt(user_input):
    matched_name = find_name_in_query(user_input, possible_names)
    if matched_name:
        docs, _ = search_documents(matched_name)
    else:
        docs, _ = search_documents(user_input)
    context = "\n".join(docs)
    if not context:
        context = "沒有找到相關資料。"
    print("context:", context)
    return f"""根據以下資料回答問題。

        【資料】
        {context}

        【問題】
        {user_input}

        請用清楚、簡潔的方式回答。"""

# 建立 API
app = Flask(__name__)

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    user_input = data.get("query", "")
    model = data.get("model", "foodsafety-bot:latest")  # 預設為 mistral
    prompt = build_prompt(user_input)
    answer = ask_ollama(prompt, model=model)
    return jsonify({"answer": answer})

if __name__ == "__main__":
    #app.run(port=5000)
    while True:
        query = input("👤 請輸入問題（輸入 exit 離開）：")
        if query.lower() == "exit":
            break
        prompt = build_prompt(query)
        answer = ask_ollama(prompt)
        print("🤖 回答：", answer)
