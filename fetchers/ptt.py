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
    "Cookie": "over18=1",  # 确保带上 over18 验证 Cookie
}


def get_latest_ptt_post(keyword):
    """抓取 PTT DC_SALE 板最新贴文（支持 ScrapingAnt 代理）"""
    target_url = f"https://www.ptt.cc/bbs/DC_SALE/search?q={urllib.parse.quote(keyword)}"

    # 优先使用 SCRAPINGANT_API_KEY，未配置时回退尝试 SCRAPER_API_KEY
    api_key = os.environ.get("SCRAPINGANT_API_KEY") or os.environ.get("SCRAPER_API_KEY")
    if api_key:
        # 使用 ScrapingAnt v2 接口，禁用无头浏览器（browser=false）提升速度
        req_url = (
            f"https://api.scrapingant.com/v2/general"
            f"?api_key={api_key}"
            f"&url={urllib.parse.quote(target_url, safe='')}"
            f"&browser=false"
        )
    else:
        req_url = target_url

    cookies = {"over18": "1"}

    try:
        # 保持 timeout=7 秒快速响应
        res = requests.get(req_url, headers=HEADERS, cookies=cookies, timeout=7)
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
