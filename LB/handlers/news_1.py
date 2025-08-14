# -*- coding: utf-8 -*-
from linebot.models import (
    FlexSendMessage, BubbleContainer, CarouselContainer,
    ImageComponent, BoxComponent, TextComponent, ButtonComponent, URIAction
)

import re
from typing import List, Dict
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# ===== 設定 =====
FDA_BASE = "https://www.fda.gov.tw"
LIST_URL = f"{FDA_BASE}/TC/news.aspx?cid=4"   # 直接使用 /TC/
PICK = 3
SNIPPET_MIN = 30
SNIPPET_MAX = 50
TIMEOUT = 12

DEFAULT_IMAGES = [
    "https://images.pexels.com/photos/161688/medical-tablets-pills-drug-161688.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2",
    "https://images.pexels.com/photos/3862603/pexels-photo-3862603.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2",
    "https://images.pexels.com/photos/6475988/pexels-photo-6475988.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2",
]

# ===== 共用會話 =====
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome Safari",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
})

# ===== 小工具 =====
_WS = re.compile(r"\s+")

def clean_and_truncate(s: str, *, min_len: int, max_len: int) -> str:
    s = _WS.sub(" ", (s or "")).strip()
    if not s or len(s) <= max_len:
        return s
    return s[:max_len] + "…"

def ensure_tc(url: str) -> str:
    return url.replace(f"{FDA_BASE}/", f"{FDA_BASE}/TC/") if "/TC/" not in url and url.startswith(FDA_BASE+"/") else url

def get_soup(url: str, *, referer: str | None = None) -> BeautifulSoup | None:
    try:
        headers = {"Referer": referer} if referer else None
        r = session.get(url, headers=headers, timeout=TIMEOUT)
        r.raise_for_status()
        if "Resource cannot be found" in r.text:
            return None
        return BeautifulSoup(r.text, "html.parser")
    except Exception:
        return None

# ===== 擷取摘要（精準容器）=====
def fetch_snippet(detail_url: str) -> str:
    soup = get_soup(detail_url, referer=LIST_URL)
    if not soup:
        return ""
    box = soup.select_one("div.edit.marginBot")
    if not box:
        return ""
    for br in box.find_all("br"):
        br.replace_with("\n")
    text = box.get_text(" ", strip=True)
    text = clean_and_truncate(text, min_len=SNIPPET_MIN, max_len=SNIPPET_MAX)
    return text

# ===== 列表抓取 =====
def fetch_latest(limit: int = PICK) -> List[Dict]:
    soup = get_soup(LIST_URL)
    if not soup:
        return []
    items: List[Dict] = []
    # 直接從列上的 a 元素回溯到 tr，抓同列的日期
    for a in soup.select('table tr td:nth-of-type(2) a[href*="newsContent.aspx"][href*="cid=4"]'):
        tr = a.find_parent("tr")
        tds = tr.find_all("td") if tr else []
        date = tds[2].get_text(strip=True) if len(tds) >= 3 else ""
        title = a.get_text(strip=True)
        url = ensure_tc(urljoin(FDA_BASE, a.get("href", "")))
        snippet = fetch_snippet(url)
        items.append({"title": title, "date": date, "url": url, "snippet": snippet})
        if len(items) >= limit:
            break
    return items

# ===== Flex 組裝 =====
def to_bubble(item: Dict, idx: int = 0) -> BubbleContainer:
    contents = [TextComponent(text=item.get("title", ""), weight="bold", size="lg", wrap=True)]
    if item.get("date"):
        contents.append(TextComponent(text=item["date"], size="xs", color="#888888", margin="sm"))
    if item.get("snippet"):
        contents.append(TextComponent(text=item["snippet"], size="sm", wrap=True, margin="md"))
    return BubbleContainer(
        hero=ImageComponent(url=DEFAULT_IMAGES[idx % len(DEFAULT_IMAGES)], size="full", aspectMode="cover"),
        body=BoxComponent(layout="vertical", contents=contents),
        footer=BoxComponent(
            layout="vertical",
            contents=[ButtonComponent(action=URIAction(label="閱讀更多", uri=item.get("url", FDA_BASE)), style="primary")]
        ),
    )

def handle(msg: str):
    if (msg or "").strip() not in ("食安新聞", "最新新聞", "新聞"):
        return None
    items = fetch_latest(PICK)
    if not items:
        return None
    bubbles = [to_bubble(it, i) for i, it in enumerate(items)]
    return FlexSendMessage(alt_text="最新食品新聞", contents=CarouselContainer(contents=bubbles))

# ===== 本機測試 =====
if __name__ == "__main__":
    data = fetch_latest(PICK)
    print("序號\t標題\t發布日期\t摘要(30~50字)")
    for i, it in enumerate(data, 1):
        print(f"{i}\t{it.get('title','')}\t{it.get('date','')}\t{it.get('snippet','')}")
