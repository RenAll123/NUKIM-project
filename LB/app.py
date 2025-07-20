from flask import Flask, request, abort
import os
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from handlers import default, faq, news
import ollama

ollama.base_url = "http://140.127.220.198:11434"

load_dotenv()
app = Flask(__name__)
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

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
            print("進入 Ollama")
            try:
                response = ollama.chat(
                    model="foodsafety-bot",
                    messages=[{"role": "user", "content": msg}]
                )
                print("Ollama 回應：", response)

                answer = response['message']['content']
                reply = TextSendMessage(text=answer)
            except Exception as e:
                print("Ollama 回應失敗：", e)
                reply = TextSendMessage(text="Ollama 模型暫時無法回應，請稍後再試。")   

    print("最後回傳內容：", reply)
    print("型別：", type(reply))    
    
    try:
        line_bot_api.reply_message(event.reply_token, reply)
    except Exception as e:
        print("LINE 回覆時發生錯誤：", e)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8082))
    app.run(host="0.0.0.0", port=port)
