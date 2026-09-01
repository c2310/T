import hashlib
import requests
from bs4 import BeautifulSoup


def get_latest_ptt_post(keyword):
    """抓取 PTT DC_SALE 板最新关键词贴文"""
    url = f"https://www.ptt.cc/bbs/DC_SALE/search?q={keyword}"
    cookies = {"over18": "1"}
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
    }

    try:
        res = requests.get(url, headers=headers, cookies=cookies, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            title_divs = soup.find_all("div", class_="title")
            for div in title_divs:
                a_tag = div.find("a")
                if a_tag and a_tag.text:
                    title = a_tag.text.strip()
                    # 排除已删文情况
                    if "(本文已被删除)" in title:
                        continue
                    href = "https://www.ptt.cc" + a_tag["href"]
                    content = f"标题: {title}\n链接: {href}"
                    content_hash = hashlib.md5(
                        content.encode("utf-8")
                    ).hexdigest()
                    return content, content_hash
        return None, None
    except Exception as e:
        print(f"[PTT 抓取异常] 关键词 '{keyword}': {e}")
        return None, None
