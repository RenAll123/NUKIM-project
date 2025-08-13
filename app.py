from flask import Flask, request, abort
import os, json
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

@app.before_request
def before_request():
    init_db()
    get_db()

@app.teardown_appcontext
def teardown(_=None):
    close_db()

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# 清理 Ollama 回應內容
def clean_response(text):
    return text.strip()

# 呼叫 Ollama
def ask_ollama(user_id, prompt):
    api_endpoint = "http://localhost:11434/api/chat"

    # 減少歷史訊息數量，提高速度
    history = fetch_history(user_id, limit_pairs=4)
    messages = history + [{"role": "user", "content": prompt}]

    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "foodsafety-bot",
        "messages": messages,
        "stream": True  # 流式
    }

    try:
        with requests.post(api_endpoint, headers=headers, json=payload, stream=True, timeout=180) as resp:
            resp.raise_for_status()
            full_reply = ""
            for line in resp.iter_lines():
                if line:
                    try:
                        data = line.decode("utf-8")
                        obj = json.loads(data)
                        if "message" in obj and "content" in obj["message"]:
                            full_reply += obj["message"]["content"]
                    except Exception as e:
                        print(f"解析流式資料錯誤: {e}")
            return clean_response(full_reply)

    except requests.exceptions.Timeout:
        return "很抱歉，Ollama 回應超時，請稍後再試。"
    except requests.exceptions.ConnectionError:
        return "很抱歉，無法連線到 Ollama 服務，請檢查服務是否啟動。"
    except Exception as e:
        return f"呼叫 Ollama 時發生錯誤: {e}"

# LINE webhook
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("LINE Signature 驗證失敗，請求被拒絕。")
        abort(400)
    return "OK", 200

# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    user_id = event.source.user_id

    # 立即回覆處理中
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="處理中，請稍候..."))

    # 後台處理
    def process_message():
        # 存使用者訊息
        add_message(user_id, "user", msg)

        # FAQ / NEWS 優先處理
        reply_content = faq.handle(msg)
        if not reply_content:
            reply_content = news.handle(msg)

        # 若沒有命中 FAQ / NEWS，就呼叫 Ollama
        if not reply_content:
            ollama_reply = ask_ollama(user_id, msg)
            reply_content = ollama_reply
            # 存模型回覆
            add_message(user_id, "assistant", ollama_reply)

        # 用 push_message 回傳給使用者
        line_bot_api.push_message(user_id, TextSendMessage(text=reply_content))

    Thread(target=process_message).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8082))
    app.run(host="0.0.0.0", port=port)

