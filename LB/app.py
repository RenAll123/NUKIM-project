from flask import Flask, request, abort
import os
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage
from handlers import default, faq, news 
import requests 
import re

load_dotenv()
app = Flask(__name__)
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# 清理 Ollama 回應內容
def clean_response(text):
    return text.strip()

def ask_ollama(prompt): 
    api_endpoint = f"http://localhost:11434/api/chat" 

    headers = {"Content-Type": "application/json"}
   
    payload = {
        "model": "foodsafety-bot",
        "messages": [{"role": "user", "content": prompt}], 
        "stream": False 
    }
    
    try:
        print(f"嘗試呼叫 Ollama API: {api_endpoint}，傳送 payload: {payload}")
        response = requests.post(api_endpoint, headers=headers, json=payload, timeout=180)
        response.raise_for_status() 

        print(f"Ollama 原始回應內容: {response.text}")
        result = response.json()
        if "message" in result and "content" in result["message"]:
            ai_reply = result["message"]["content"]
            ai_reply = clean_response(ai_reply)
            return ai_reply
        else:
            print(f"Ollama 回應格式不符合預期或內容缺失: {result}")
            return "很抱歉，Ollama 回應格式錯誤或內容缺失。"

    except requests.exceptions.Timeout:
        print("Ollama 請求超時。")
        return "很抱歉，Ollama 回應超時，請稍後再試。"
    except requests.exceptions.ConnectionError as e:
        print(f"Ollama 連線錯誤：{e}。請確認 ngrok 隧道是否運行中，以及 URL 是否正確。")
        return "很抱歉，無法連線到 Ollama 服務。請確認隧道狀態。"
    except requests.exceptions.HTTPError as e:
        print(f"Ollama HTTP 錯誤：{e.response.status_code} - {e.response.text}")
        return f"Ollama 服務錯誤：{e.response.status_code}，請檢查 Ollama 主機。"
    except ValueError as e:
        print(f"Ollama 回應 JSON 解析錯誤：{e}")
        return "Ollama 回應格式錯誤，無法解析。"
    except Exception as e:
        print(f"呼叫 Ollama 時發生未預期錯誤：{e}")
        return "很抱歉，Ollama 服務發生未知錯誤。"


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

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    print(f"收到訊息：{repr(msg)}")

    reply_content = None
    
    reply_content = faq.handle(msg)
    if reply_content:
        print("FAQ 命中")
    else:
        reply_content = news.handle(msg)
        if reply_content:
            print("NEWS 命中")
        else:
            print("進入 Ollama 處理")
            try:
                ollama_response_text = ask_ollama(msg)
                reply_content = ollama_response_text
            except Exception as e:
                print(f"呼叫 ask_ollama 失敗：{e}")
                reply_content = "Ollama 模型暫時無法回應，請稍後再試。"
    
    
    if reply_content is None:
        reply_content = "很抱歉，我無法理解您的問題，請嘗試其他問題。"

    if isinstance(reply_content, (TextSendMessage, FlexSendMessage)):
        final_reply_message = reply_content
    else:
        final_reply_message = TextSendMessage(text=str(reply_content))

    print("最後回傳內容：", final_reply_message)
    print("型別：", type(final_reply_message))
    
    try:
        line_bot_api.reply_message(event.reply_token, final_reply_message)
    except Exception as e:
        print(f"LINE 回覆時發生錯誤：{e}")

        print(f"LINE API 錯誤詳細: {e}, Event source: {event.source}, Reply token: {event.reply_token}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8082))
    app.run(host="0.0.0.0", port=port)

