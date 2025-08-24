from flask import Flask, request, abort
import os
import threading
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError
from handlers import faq, news
from memory import init_db, add_message, fetch_history
import requests
import json

load_dotenv()
app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# 啟動時初始化資料庫（建立表，不會清空資料）
with app.app_context():
    init_db()

# 清理模型回覆
def clean_response(text):
    return text.strip()

# 呼叫 Ollama（背景 Thread，串流 + 限制歷史對話）
def call_ollama_and_push(user_id, prompt):
    with app.app_context():
        try:
            # 限制歷史對話為最近 4 對話
            history = fetch_history(user_id, limit_pairs=4)
            messages = history + [{"role": "user", "content": prompt}]

            payload = {
                "model": "foodsafety_small",
                "messages": messages,
                "stream": True  # 串流模式
            }

            api_endpoint = "http://127.0.0.1:11434/api/chat"
            response = requests.post(api_endpoint, json=payload, stream=True, timeout=600)

            answer = ""
            for line in response.iter_lines():
                if line:
                    data = json.loads(line.decode("utf-8"))
                    if "message" in data and "content" in data["message"]:
                        partial = data["message"]["content"]
                        answer += partial
                        # 可選：即時邊推送部分回覆
                        # line_bot_api.push_message(user_id, TextSendMessage(text=partial))

            answer = clean_response(answer)

            # 存入資料庫
            add_message(user_id, "assistant", answer)
            # 推送完整回覆
            line_bot_api.push_message(user_id, TextSendMessage(text=answer))

        except Exception as e:
            line_bot_api.push_message(user_id, TextSendMessage(text=f"Ollama 回覆失敗: {e}"))

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    user_id = event.source.user_id

    # 先嘗試 FAQ
    reply_content = faq.handle(msg)
    if reply_content:
        line_bot_api.reply_message(event.reply_token, reply_content)
        return

    # 嘗試 NEWS
    reply_content = news.handle(msg)
    if reply_content:
        line_bot_api.reply_message(event.reply_token, reply_content)
        return

    # 走 Ollama 流程
    add_message(user_id, "user", msg)

    # 立即回覆「處理中」
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="處理中，請稍候...")
    )

    # 背景呼叫 Ollama
    threading.Thread(target=call_ollama_and_push, args=(user_id, msg)).start()

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8082))
    app.run(host="0.0.0.0", port=port)

