import hashlib
import os
import urllib.parse
from bs4 import BeautifulSoup
import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
}


def get_latest_yahoo_post(keyword):
    """抓取 Yahoo 奇摩拍卖最新商品（支持 ScraperAPI 代理）"""
    encoded_kw = urllib.parse.quote(keyword)
    target_url = f"https://tw.bid.yahoo.com/search/auction/product?p={encoded_kw}&sort=-curprice"

    api_key = os.environ.get("SCRAPER_API_KEY")
    if api_key:
        req_url = f"http://api.scraperapi.com?api_key={api_key}&url={urllib.parse.quote(target_url)}"
    else:
        req_url = target_url

    try:
        res = requests.get(req_url, headers=HEADERS, timeout=20)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            items = soup.find_all(
                "a", href=lambda h: h and "/item/" in h and "item" in h
            )
            for item in items:
                title = item.get_text(strip=True)
                if len(title) > 5:
                    href = item["href"]
                    content = f"商品: {title}\n链接: {href}"
                    content_hash = hashlib.md5(content.encode("utf-8")).hexdigest()
                    return content, content_hash
        return None, None
    except Exception as e:
        print(f"[Yahoo 抓取异常] 关键词 '{keyword}': {e}")
        return None, None
