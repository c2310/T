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


def get_latest_ptt_post(keyword):
    """抓取 PTT DC_SALE 板最新贴文（支持 ScraperAPI 代理）"""
    target_url = f"https://www.ptt.cc/bbs/DC_SALE/search?q={urllib.parse.quote(keyword)}"

    api_key = os.environ.get("SCRAPER_API_KEY")
    if api_key:
        # PTT 需要通过 cookies 绕过 18 岁提示，代理时可以通过请求参数传递
        req_url = f"http://api.scraperapi.com?api_key={api_key}&url={urllib.parse.quote(target_url)}&keep_headers=true"
    else:
        req_url = target_url

    cookies = {"over18": "1"}

    try:
        res = requests.get(req_url, headers=HEADERS, cookies=cookies, timeout=20)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
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
        print(f"[PTT 抓取异常] 关键词 '{keyword}': {e}")
        return None, None
