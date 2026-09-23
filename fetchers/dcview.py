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
    encoded_kw = urllib.parse.quote(keyword)
    target_url = f"https://market.dcview.com/search/{encoded_kw}"

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

    try:
        res = requests.get(req_url, headers=req_headers, timeout=15)
        
        if res.status_code != 200:
            print(f"[DCView 响应异常] 关键词: {keyword} | 状态码: {res.status_code} | 返回信息: {res.text[:150]}")
            return None, None

        if api_key:
            try:
                html_text = res.json().get("content", "")
            except Exception:
                html_text = res.text
        else:
            html_text = res.text

        soup = BeautifulSoup(html_text, "html.parser")
        items = soup.find_all("a", href=lambda h: h and "/post/" in h)

        for item in items:
            title = item.get_text(strip=True)
            if len(title) > 3 and not any(k in title for k in ["买", "徵", "征", "收"]):
                href = item["href"]
                if not href.startswith("http"):
                    href = "https://market.dcview.com" + href
                content = f"标题: {title}\n链接: {href}"
                content_hash = hashlib.md5(content.encode("utf-8")).hexdigest()
                return content, content_hash
        return None, None
    except Exception as e:
        print(f"[DCView] 抓取网络异常 '{keyword}': {e}")
        return None, None
