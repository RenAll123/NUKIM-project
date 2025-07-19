from linebot.models import (
    FlexSendMessage, BubbleContainer, CarouselContainer,
    ImageComponent, BoxComponent, TextComponent, ButtonComponent,
    URIAction
)

def handle(msg):
    print(f"[news.handle] 收到 msg：{repr(msg)}")

    msg = msg.strip()

    if msg not in ["食安新聞"]:
        return None

    bubbles = []

    bubbles.append(BubbleContainer(
        hero=ImageComponent(
            url="https://images.pexels.com/photos/161688/medical-tablets-pills-drug-161688.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2",
            size="full",
            aspectMode="cover"
        ),
        body=BoxComponent(
            layout="vertical",
            contents=[
                TextComponent(text="公告修正「健康食品之骨質保健功效評估方法」", weight="bold", size="lg", wrap=True),
                TextComponent(text="為使健康食品保健功效評估試驗之實驗方法與實驗執行相關規範更臻明確與周全...", wrap=True, size="sm", margin="md")
            ]
        ),
        footer=BoxComponent(
            layout="vertical",
            contents=[
                ButtonComponent(
                    action=URIAction(label="閱讀更多", uri="https://www.fda.gov.tw/tc/newsContent.aspx?cid=4&id=t623505"),
                    style="primary"
                )
            ]
        )
    ))

    bubbles.append(BubbleContainer(
        hero=ImageComponent(
            url="https://images.pexels.com/photos/3862603/pexels-photo-3862603.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2",
            size="full",
            aspectMode="cover"
        ),
        body=BoxComponent(
            layout="vertical",
            contents=[
                TextComponent(text="食藥署說明今日媒體報導「藥界籲縮短藥品入庫效期」一事", weight="bold", size="lg", wrap=True),
                TextComponent(text="有關今日多家媒體報導「藥界籲縮短藥品入庫效期」一事，食品藥物管理署(以下簡稱食藥署)說明如下...", wrap=True, size="sm", margin="md")
            ]
        ),
        footer=BoxComponent(
            layout="vertical",
            contents=[
                ButtonComponent(
                    action=URIAction(label="閱讀更多", uri="https://www.fda.gov.tw/tc/newsContent.aspx?cid=4&id=t623490"),
                    style="primary"
                )
            ]
        )
    ))
    
    bubbles.append(BubbleContainer(
        hero=ImageComponent(
            url="https://images.pexels.com/photos/6475988/pexels-photo-6475988.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2",
            size="full",
            aspectMode="cover"
        ),
        body=BoxComponent(
            layout="vertical",
            contents=[
                TextComponent(text="安心對抗青春痘「藥」這樣用！", weight="bold", size="lg", wrap=True),
                TextComponent(text="青春痘（痤瘡）是常見的皮膚問題，春夏交替時，溫度和濕度變化易加重不適...", wrap=True, size="sm", margin="md")
            ]
        ),
        footer=BoxComponent(
            layout="vertical",
            contents=[
                ButtonComponent(
                    action=URIAction(label="閱讀更多", uri="https://www.fda.gov.tw/tc/newsContent.aspx?cid=4&id=t623502"),
                    style="primary"
                )
            ]
        )
    ))

    carousel = CarouselContainer(contents=bubbles)
    return FlexSendMessage(alt_text="最新食品新聞", contents=carousel)