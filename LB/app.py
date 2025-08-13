from flask import Flask, request, abort
import os
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from handlers import default, faq, news
import requests
from threading import Thread
from memory import init_db, get_db, close_db, add_message, fetch_history

load_dotenv()
app = Flask(__name__)

# 初始化 DB
@app.before_request
def before_request():
    init_db()
    get_db()

@app.teardown_appcontext
def teardown(_=None):
    close_db()

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# 清理 Ollama 回應
def clean_response(text):
    return text.strip()

def ask_ollama(user_id, prompt):
    api_endpoint = "http://localhost:11434/api/chat"
    history = fetch_history(user_id, limit_pairs=8)
    messages = history + [{"role": "user", "content": prompt}]

    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "foodsafety-bot",
        "messages": messages,
        "stream": False
    }

    try:
        response = requests.post(api_endpoint, headers=headers, json=payload, timeout=180)
        response.raise_for_status()
        result = response.json()

        if "message" in result and "content" in result["message"]:
            return clean_response(result["message"]["content"])
        else:
            return "很抱歉，Ollama 回應格式錯誤或內容缺失。"

    except requests.exceptions.Timeout:
        return "很抱歉，Ollama 回應超時，請稍後再試。"
    except requests.exceptions.ConnectionError:
        return "很抱歉，無法連線到 Ollama 服務，請確認 Ollama 是否啟動。"
    except Exception as e:
        print(f"Ollama 呼叫錯誤: {e}")
        return "很抱歉，Ollama 服務發生未知錯誤。"

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK", 200

def process_message(user_id, msg):
    with app.app_context():  # Thread 中建立 Flask 上下文
        try:
            add_message(user_id, "user", msg)

            # 先處理 FAQ / NEWS
            reply_content = faq.handle(msg)
            if not reply_content:
                reply_content = news.handle(msg)

            # 若無命中，呼叫 Ollama
            if not reply_content:
                ollama_reply = ask_ollama(user_id, msg)
                reply_content = ollama_reply
                add_message(user_id, "assistant", ollama_reply)

            line_bot_api.push_message(user_id, TextSendMessage(text=str(reply_content)))
        except Exception as e:
            print(f"Thread 處理訊息錯誤: {e}")

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    user_id = event.source.user_id

    print(f"收到訊息：{repr(msg)}")

    # 立即回覆「處理中」避免 webhook 超時
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="處理中，請稍候..."))

    # 背景 Thread 處理
    Thread(target=process_message, args=(user_id, msg)).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8082))
    app.run(host="0.0.0.0", port=port)

