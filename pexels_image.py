# -*- coding: utf-8 -*-
import os, re, hashlib
from datetime import datetime
from typing import Optional, List
import requests

# 選擇性裁切成 1280x720，需要 Pillow
try:
    from PIL import Image
    _HAS_PIL = True
except Exception:
    _HAS_PIL = False

PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static", "gen")
os.makedirs(STATIC_DIR, exist_ok=True)

TARGET_W, TARGET_H = 1280, 720
_STOPWORDS = set("的 了 和 與 及 而 並 在 有 於 是 為 被 或 者 以及 相關 最新 官方 公告 新聞".split())
_WORD_RE = re.compile(r"[A-Za-z0-9]+|[\u4e00-\u9fff]{1,4}")

def _build_query(title: str, snippet: str) -> str:
    text = f"{title} {snippet}".strip()
    if not text:
        return "food safety"
    toks = _WORD_RE.findall(text)
    keep: List[str] = []
    for t in toks:
        if t.lower() in _STOPWORDS: 
            continue
        if re.match(r"[A-Za-z0-9]+", t) or len(t) >= 2:
            keep.append(t)
    return " ".join(keep[:8]) or "food safety"

def _fname(key: str) -> str:
    today = datetime.now().strftime("%Y%m%d")
    h = hashlib.sha1((key + today).encode()).hexdigest()[:10]
    return f"{today}-{h}.jpg"

def _download(url: str, out_path: str) -> bool:
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        with open(out_path, "wb") as f:
            f.write(r.content)
        return True
    except Exception:
        return False

def _crop_16_9(path: str):
    if not _HAS_PIL: return
    try:
        with Image.open(path) as im:
            w, h = im.size
            if w <= 0 or h <= 0: return
            target_ratio = TARGET_W / TARGET_H
            ratio = w / h
            if abs(ratio - target_ratio) > 1e-3:
                if ratio > target_ratio:
                    new_w = int(h * target_ratio)
                    x0 = (w - new_w) // 2
                    box = (x0, 0, x0 + new_w, h)
                else:
                    new_h = int(w / target_ratio)
                    y0 = (h - new_h) // 2
                    box = (0, y0, w, y0 + new_h)
                im = im.crop(box)
            im = im.resize((TARGET_W, TARGET_H), Image.LANCZOS)
            im.save(path, "JPEG", quality=92, optimize=True)
    except Exception:
        pass

def _search_pexels(q: str) -> Optional[str]:
    if not PEXELS_API_KEY: return None
    headers = {"Authorization": PEXELS_API_KEY}
    params = {"query": q, "orientation": "landscape", "per_page": 24, "size": "large"}
    try:
        r = requests.get("https://api.pexels.com/v1/search", headers=headers, params=params, timeout=12)
        r.raise_for_status()
        data = r.json()
        photos = data.get("photos") or []
        if not photos: return None
        # 挑最接近 16:9 的一張
        best_url, best_diff = None, 999
        for p in photos:
            w, h = p.get("width") or 0, p.get("height") or 0
            src = (p.get("src") or {}).get("large2x") or (p.get("src") or {}).get("original")
            if not src or not w or not h: continue
            diff = abs((w/h) - (16/9))
            if diff < best_diff:
                best_diff, best_url = diff, src
        return best_url
    except Exception:
        return None

def get_image_for_news(title: str, snippet: str) -> Optional[str]:
    """ 從 Pexels 搜圖→存檔→回傳可公開 URL """
    if not PUBLIC_BASE_URL or not PEXELS_API_KEY:
        return None
    q = _build_query(title, snippet)
    fname = _fname(q + "|" + title)
    out_path = os.path.join(STATIC_DIR, fname)

    if os.path.isfile(out_path):
        return f"{PUBLIC_BASE_URL}/static/gen/{fname}"

    src = _search_pexels(q)
    if not src: return None
    if not _download(src, out_path): return None

    _crop_16_9(out_path)
    return f"{PUBLIC_BASE_URL}/static/gen/{fname}"
