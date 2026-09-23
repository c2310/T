import hashlib
import os
import urllib.parse
from bs4 import BeautifulSoup
import requests


def get_latest_dcview_post(keyword):
    encoded_kw = urllib.parse.quote(keyword)
    target_url = f"https://market.dcview.com/search/{encoded_kw}"

    api_key = os.environ.get("SCRAPINGANT_API_KEY") or os.environ.get("SCRAPER_API_KEY")
    if api_key:
        req_url = f"https://api.scrapingant.com/v2/general?api_key={api_key}&url={urllib.parse.quote(target_url, safe='')}&browser=false"
    else:
        req_url = target_url

    try:
        res = requests.get(req_url, timeout=12)
        
        # 调试关键点：如果不等于 200，立刻打印原因
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
