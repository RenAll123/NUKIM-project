from linebot.models import TextSendMessage, FlexSendMessage

def handle(msg):
    msg = msg.strip()

    if msg in ["常見問題"]:
        flex_content = {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "常見問題",
                        "weight": "bold",
                        "size": "lg",
                        "margin": "md"
                    },
                    {
                        "type": "button",
                        "action": {
                            "type": "message",
                            "label": "什麼是食品添加物？",
                            "text": "我想知道「什麼是食品添加物」"
                        },
                        "style": "link"
                    },
                    {
                        "type": "button",
                        "action": {
                            "type": "message",
                            "label": "常見的食品添加物？",
                            "text": "我想知道「常見的食品添加物」"
                        },
                        "style": "link"
                    },
                    {
                        "type": "button",
                        "action": {
                            "type": "message",
                            "label": "對食品安全有疑慮怎麼辦？",
                            "text": "我想知道「對食品安全有疑慮怎麼辦」"
                        },
                        "style": "link"
                    },
                    {
                        "type": "button",
                        "action": {
                            "type": "message",
                            "label": "什麼是無添加驗證/潔淨標章？",
                            "text": "我想知道「什麼是無添加驗證/潔淨標章」"
                        },
                        "style": "link"
                    }
                ]
            }
        }
        return FlexSendMessage(alt_text="常見問題", contents=flex_content)

    elif msg == "我想知道「什麼是食品添加物」":
        return TextSendMessage(text="食品添加物是指為了改善食品的色、香、味、口感、保存期限等，而額外加入食品中的物質，例如防腐劑、色素、甜味劑、抗氧化劑等。")

    elif msg == "我想知道「常見的食品添加物」":
        return TextSendMessage(text="防腐劑：防止食品腐爛變質，防止微生物的生長，有效延長保存期限；抗氧化劑：抗氧化劑防止食品中的油脂氧化；著色劑（色素）：用來提升食品的外觀，改善加工過程中的食物褪色，使其更具吸引力；調味劑：調味劑用來增強食品的風味，調整食物的味道，使其更加美味。")

    elif msg == "我想知道「對食品安全有疑慮怎麼辦」":
        return TextSendMessage(text="如果您有食品檢舉、食品諮詢、消費問題、中小企業諮詢、生鮮農產諮詢等食品安全相關問題，以市話或手機直撥「1919」，可得到即時服務與處理。")

    elif msg == "我想知道「什麼是無添加驗證/潔淨標章」":
        return TextSendMessage(text="藉由A.A.(無添加協會)進行檢核機制，透過第三方審查與評核，合格後所獲得之標章，以六大類食品添加物為驗證標準，無含有鮮味劑、漂白劑、品質改良劑、人工色素、人工香精及防腐劑；證書有效期為一年，期間包含不定期追蹤查核，若不符合審查標準，證書即廢止。自廢止日起一年後，始得再提出申請。")

    return None