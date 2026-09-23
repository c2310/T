import hashlib
import os
import time
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
    encoded_kw = urllib.parse.quote(keyword)
    # 修改 1：将 sort=-curprice 改为 sort=-pubtime，按最新上架时间排序
    target_url = f"https://tw.bid.yahoo.com/search/auction/product?p={encoded_kw}&sort=-pubtime"

    api_key = os.environ.get("SCRAPINGANT_API_KEY") or os.environ.get("SCRAPER_API_KEY")

    if api_key:
        req_url = (
            f"https://api.scrapingant.com/v2/general"
            f"?url={urllib.parse.quote(target_url, safe='')}"
            f"&browser=false"
        )
        req_headers = {"x-api-key": api_key}
    else:
        req_url = target_url
        req_headers = HEADERS

    # 修改 2：增加重试机制，应对 ScrapingAnt 免费版的 409 并发限制
    for attempt in range(2):
        try:
            res = requests.get(req_url, headers=req_headers, timeout=30)

            # 触发 409 并发限制时，等待 4 秒后自动重试
            if res.status_code == 409 and attempt == 0:
                time.sleep(4)
                continue

            if res.status_code != 200:
                print(f"[Yahoo 响应异常] 关键词: {keyword} | 状态码: {res.status_code} | 返回信息: {res.text[:150]}")
                return None, None

            if api_key:
                try:
                    html_text = res.json().get("content", "")
                except Exception:
                    html_text = res.text
            else:
                html_text = res.text

            soup = BeautifulSoup(html_text, "html.parser")
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
            if attempt == 0:
                time.sleep(3)
                continue
            print(f"[Yahoo 抓取异常] 关键词 '{keyword}': {e}")
            return None, None

    return None, None
