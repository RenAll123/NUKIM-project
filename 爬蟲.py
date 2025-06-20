import requests
from bs4 import BeautifulSoup
import pandas as pd
import random
import re

#使用者標籤
user_agents = [
"Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; AcooBrowser; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
"Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; Acoo Browser; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.0.04506)",
"Mozilla/4.0 (compatible; MSIE 7.0; AOL 9.5; AOLBuild 4337.35; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
"Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)",
"Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 2.0.50727; Media Center PC 6.0)",
"Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 1.0.3705; .NET CLR 1.1.4322)",
"Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.2; .NET CLR 1.1.4322; .NET CLR 2.0.50727; InfoPath.2; .NET CLR 3.0.04506.30)",
"Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN) AppleWebKit/523.15 (KHTML, like Gecko, Safari/419.3) Arora/0.3 (Change: 287 c9dfb30)",
"Mozilla/5.0 (X11; U; Linux; en-US) AppleWebKit/527+ (KHTML, like Gecko, Safari/419.3) Arora/0.6",
"Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.2pre) Gecko/20070215 K-Ninja/2.1.1",
"Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9) Gecko/20080705 Firefox/3.0 Kapiko/3.0",
"Mozilla/5.0 (X11; Linux i686; U;) Gecko/20070322 Kazehakase/0.4.5",
"Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.8) Gecko Fedora/1.9.0.8-1.fc10 Kazehakase/0.5.6",
"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11",
"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3) AppleWebKit/535.20 (KHTML, like Gecko) Chrome/19.0.1036.7 Safari/535.20",
"Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; fr) Presto/2.9.168 Version/11.52",
    ]

title_list = []
date_list = []
link_list = []
content_list = []

#pn是頁數
for page in range(1,6):
    url = "https://www.fda.gov.tw/tc/news.aspx?cid=4&pn="+str(page)

    headers = {
        "user-agent":random.choice(user_agents)
    }

    resp =requests.get(url, headers = headers)

    soup = BeautifulSoup(resp.text,"lxml")
    elem = soup.select(".listTable")

    for e in elem:
        links = [i.get('href') for i in e.select("a")]
        for link in links:
            resp = requests.get("https://www.fda.gov.tw/tc/" + link, headers=headers)
            soup = BeautifulSoup(resp.text, "lxml")
            # 標題
            data_title_elem = soup.select(".dataTitle")
            title = ""
            date = ""
            if data_title_elem:
                f = data_title_elem[0]
                titles = [title.text for title in f.select(".fdtitle")]
                title = titles[0] if titles else ""
                # 日期
                orange_texts = f.select(".orangeText")
                found_date = ""
                for orange in orange_texts:
                    text = orange.text
                    found_dates = re.findall(r"\d{4}-\d{2}-\d{2}", text)
                    if found_dates:
                        found_date = found_dates[0]
                        break
                date = found_date
            #內容
            content_elem = soup.select(".edit.marginBot")
            content = content_elem[0].text if content_elem else ""
            content = content.replace('\n', '').replace('\r', '')  # 移除換行符號
            # append
            title_list.append(title)
            content_list.append(content)
            date_list.append(date)
            link_list.append("https://www.fda.gov.tw/tc/"+link)

df = pd.DataFrame()
df["title"] = title_list
df["content"] = content_list
df["date"] = date_list
df["link"] = link_list
#print(df)
df.to_csv("./df_news.csv", encoding="utf-8-sig")