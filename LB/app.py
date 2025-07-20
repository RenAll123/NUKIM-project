from flask import Flask, request, abort
import os
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from handlers import default, faq, news
import ollama
import requests

load_dotenv()
app = Flask(__name__)
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

def query_ollama_by_webhook(question: str) -> str:
    try:
        res = requests.post(
            "http://140.127.220.198:8001/ask",  
            json={"question": question},
            timeout=15
        )
        res.raise_for_status()
        data = res.json()
        return data.get("answer", "主機回傳格式有誤。")
    except Exception as e:
        print("Webhook 呼叫失敗：", e)
        return "後端主機暫時無法回應，請稍後再試。"

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK", 200

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    print(f"收到訊息：{repr(msg)}")

    reply = faq.handle(msg)
    if reply:
        print("FAQ 命中")
    else:
        reply = news.handle(msg)
        if reply:
            print("NEWS 命中")
        else:
            print("進入 webhook 模式詢問主機")
            answer = query_ollama_by_webhook(msg)
            reply = TextSendMessage(text=answer)

    print("最後回傳內容：", reply)
    print("型別：", type(reply))    
    
    try:
        line_bot_api.reply_message(event.reply_token, reply)
    except Exception as e:
        print("LINE 回覆時發生錯誤：", e)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8082))
    app.run(host="0.0.0.0", port=port)
