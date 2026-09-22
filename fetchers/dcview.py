import hashlib
import os
import urllib.parse
from bs4 import BeautifulSoup
import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
}


def get_latest_dcview_post(keyword):
    """抓取 DCView 二手相机最新贴文（支持 ScraperAPI 代理）"""
    encoded_kw = urllib.parse.quote(keyword)
    target_url = f"https://market.dcview.com/search/{encoded_kw}"

    api_key = os.environ.get("SCRAPER_API_KEY")
    if api_key:
        req_url = f"http://api.scraperapi.com?api_key={api_key}&url={urllib.parse.quote(target_url)}"
    else:
        req_url = target_url

    try:
        # 将 timeout 压缩至 7 秒，避免因个别代理请求拖慢整个线程池
        res = requests.get(req_url, headers=HEADERS, timeout=7)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            items = soup.find_all("a", href=lambda h: h and "/post/" in h)

            for item in items:
                title = item.get_text(strip=True)
                # 过滤征求贴（买、徵、徵求、收），仅保留卖帖
                if len(title) > 3 and not any(k in title for k in ["买", "徵", "征", "收"]):
                    href = item["href"]
                    if not href.startswith("http"):
                        href = "https://market.dcview.com" + href
                    content = f"标题: {title}\n链接: {href}"
                    content_hash = hashlib.md5(content.encode("utf-8")).hexdigest()
                    return content, content_hash
        return None, None
    except Exception as e:
        print(f"[DCView] 抓取异常 关键词 '{keyword}': {e}")
        return None, None
