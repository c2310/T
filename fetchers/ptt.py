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
    "Cookie": "over18=1",
}


def get_latest_ptt_post(keyword):
    target_url = f"https://www.ptt.cc/bbs/DC_SALE/search?q={urllib.parse.quote(keyword)}"

    api_key = os.environ.get("SCRAPINGANT_API_KEY") or os.environ.get("SCRAPER_API_KEY")

    if api_key:
        req_url = (
            f"https://api.scrapingant.com/v2/general"
            f"?url={urllib.parse.quote(target_url, safe='')}"
            f"&browser=false"
            f"&cookies=over18%3D1"
        )
        req_headers = {"x-api-key": api_key}
        cookies = None
    else:
        req_url = target_url
        req_headers = HEADERS
        cookies = {"over18": "1"}

    for attempt in range(2):
        try:
            res = requests.get(req_url, headers=req_headers, cookies=cookies, timeout=30)

            if res.status_code == 409 and attempt == 0:
                time.sleep(4)
                continue

            if res.status_code != 200:
                print(f"[PTT 响应异常] 关键词: {keyword} | 状态码: {res.status_code} | 返回信息: {res.text[:150]}")
                return None, None

            if api_key:
                try:
                    html_text = res.json().get("content", "")
                except Exception:
                    html_text = res.text
            else:
                html_text = res.text

            soup = BeautifulSoup(html_text, "html.parser")
            title_divs = soup.find_all("div", class_="title")
            for div in title_divs:
                a_tag = div.find("a")
                if a_tag and a_tag.text:
                    title = a_tag.text.strip()
                    if "(本文已被删除)" in title:
                        continue
                    href = "https://www.ptt.cc" + a_tag["href"]
                    content = f"标题: {title}\n链接: {href}"
                    content_hash = hashlib.md5(content.encode("utf-8")).hexdigest()
                    return content, content_hash
            return None, None

        except Exception as e:
            if attempt == 0:
                time.sleep(3)
                continue
            print(f"[PTT 抓取异常] 关键词 '{keyword}': {e}")
            return None, None

    return None, None
