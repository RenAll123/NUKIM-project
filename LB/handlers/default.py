from linebot.models import TextSendMessage

def fallback(msg):
    return TextSendMessage(
        text="我還不太懂你的意思...\n請點選選單中的圖片，或輸入關鍵字來讓我更好理解你的需求！"
    )