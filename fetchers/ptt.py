import hashlib
import urllib.parse
import requests
from bs4 import BeautifulSoup


def get_latest_ptt_post(keyword):
    """抓取 PTT DC_SALE 版面最新贴文"""
    encoded_kw = urllib.parse.quote(keyword)
    url = f"https://www.ptt.cc/bbs/DC_SALE/search?q={encoded_kw}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
    }
    cookies = {"over18": "1"}

    try:
        response = requests.get(
            url, headers=headers, cookies=cookies, timeout=12
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        rents = soup.find_all("div", class_="r-ent")
        if not rents:
            return None, None

        for rent in reversed(rents):
            title_div = rent.find("div", class_="title")
            if title_div and title_div.find("a"):
                a_tag = title_div.find("a")
                title = a_tag.text.strip()
                href = "https://www.ptt.cc" + a_tag["href"]
                content = f"标题: {title}\n链接: {href}"
                content_hash = hashlib.md5(content.encode("utf-8")).hexdigest()
                return content, content_hash

        return None, None
    except Exception as e:
        print(f"[PTT 抓取异常] 关键词 '{keyword}': {e}")
        return None, None
