from flask import Flask, request, abort
import os
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from handlers import default, faq, news
import requests 
import re

load_dotenv()
app = Flask(_name_)
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

def ask_ollama(prompt):
    ngrok_url = "https://672476f15a8c.ngrok-free.app"
    api_endpoint = f"{ngrok_url}/api/chat" 
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "foodsafety-bot",
        "messages": [{"role": "user", "content": prompt_text}],
        "stream": False
    }

     try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        print(f"Ollama 回應內容: {response.text}")
        result = response.json()
        ai_reply = result.get("response", "很抱歉，AI 回覆失敗了喔。")
        ai_reply = clean_response(ai_reply)
        return ai_reply
    except requests.exceptions.RequestException as e:
        print(f"Ollama 請求錯誤：{e}")
        return "很抱歉，無法聯繫 Ollama。"
    except ValueError as e:
        print(f"Ollama 回應錯誤：{e}")
        return "Ollama 回應格式錯誤。"


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
                ollama_response_text = ask_ollama(msg)
                reply_content = ollama_response_text
            except Exception as e:
                print("Ollama 回應失敗：", e)
                reply_content = "Ollama 模型暫時無法回應，請稍後再試。"   
    
    if reply_content is None:
        reply_content = "很抱歉，我無法理解您的問題，請嘗試其他問題。"

    final_reply_message = TextSendMessage(text=reply_content)
    print("最後回傳內容：", reply)
    print("型別：", type(reply))    
    
    try:
        line_bot_api.reply_message(event.reply_token, reply)
    except Exception as e:
        print("LINE 回覆時發生錯誤：", e)

if _name_ == "_main_":
    port = int(os.environ.get("PORT", 8082))
    app.run(host="0.0.0.0", port=port)
