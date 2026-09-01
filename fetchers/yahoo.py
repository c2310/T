import hashlib
import urllib.parse
import requests
from bs4 import BeautifulSoup


def get_latest_yahoo_post(keyword):
    """抓取 Yahoo 奇摩拍卖最新商品"""
    encoded_kw = urllib.parse.quote(keyword)
    url = f"https://tw.bid.yahoo.com/search/auction/product?p={encoded_kw}&sort=-curprice"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
    }

    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            # 匹配拍卖商品卡片
            items = soup.find_all(
                "a", href=lambda h: h and "/item/" in h and "item" in h
            )
            for item in items:
                title = item.get_text(strip=True)
                if len(title) > 5:
                    href = item["href"]
                    content = f"商品: {title}\n链接: {href}"
                    content_hash = hashlib.md5(
                        content.encode("utf-8")
                    ).hexdigest()
                    return content, content_hash
        return None, None
    except Exception as e:
        print(f"[Yahoo 抓取异常] 关键词 '{keyword}': {e}")
        return None, None
