from flask import Flask, request, abort
import os
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage
from handlers import default, faq, news 
import requests 
import re
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

    # 減少歷史數量以加速
    history = fetch_history(user_id, limit_pairs=4)
    messages = history + [{"role": "user", "content": prompt}]

    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "foodsafety-bot",
        "messages": messages,
        "stream": False
    }

    try:
        print(f"[ask_ollama] payload: model={payload['model']} messages_len={len(messages)}")
        response = requests.post(api_endpoint, headers=headers, json=payload, timeout=180)
        response.raise_for_status()
        # debug print raw text
        print(f"[ask_ollama] raw response: {response.text[:400]}")  # 只印前400字
        data = response.json()

        if "message" in data and "content" in data["message"]:
            ai_reply = data["message"]["content"]
            return clean_response(ai_reply)
        # 兼容不同回傳格式（有些 Ollama 版本回傳 messages 列表）
        if "messages" in data and isinstance(data["messages"], list) and len(data["messages"])>0:
            last = data["messages"][-1]
            if "content" in last:
                return clean_response(last["content"])

        print(f"[ask_ollama] Unexpected response shape: {data}")
        return "很抱歉，Ollama 回應格式錯誤或內容缺失。"

    except requests.exceptions.Timeout:
        print("[ask_ollama] Timeout calling Ollama")
        return "很抱歉，Ollama 回應超時，請稍後再試。"
    except requests.exceptions.ConnectionError as e:
        print(f"[ask_ollama] ConnectionError: {e}")
        return "很抱歉，無法連線到 Ollama 服務，請檢查服務是否啟動。"
    except Exception as e:
        # 把完整例外印出來，方便 debug
        import traceback
        traceback.print_exc()
        print(f"[ask_ollama] Unexpected error: {e}")
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

    # 先嘗試 FAQ / NEWS（保留你原邏輯）
    reply_content = faq.handle(msg)
    if reply_content:
        print("FAQ 命中")
    else:
        reply_content = news.handle(msg)
        if reply_content:
            print("NEWS 命中")
        else:
            print("進入 Ollama 處理")
            user_id = event.source.user_id

            # 存使用者訊息（保證先記錄）
            try:
                add_message(user_id, "user", msg)
            except Exception as e:
                print(f"[handle_message] add_message(user) failed: {e}")

            # 呼叫 Ollama（注意傳入 user_id）
            try:
                ollama_response_text = ask_ollama(user_id, msg)
                reply_content = ollama_response_text
                # 存模型回覆
                try:
                    add_message(user_id, "assistant", reply_content)
                except Exception as e:
                    print(f"[handle_message] add_message(assistant) failed: {e}")
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
