import hashlib
import os
import time
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
    # 修改 1：拼接 sort 参数，强制要求 DCView 按照最新发布时间倒序排列
    target_url = f"https://market.dcview.com/search/{encoded_kw}?sort=created_at_desc"

    api_key = os.environ.get("SCRAPINGANT_API_KEY") or os.environ.get("SCRAPER_API_KEY")

    if api_key:
        # 修改 2：将 browser=false 改为 browser=true，借助无头浏览器绕过 DCView 的 404 防火墙拦截
        req_url = (
            f"https://api.scrapingant.com/v2/general"
            f"?url={urllib.parse.quote(target_url, safe='')}"
            f"&browser=true"
        )
        req_headers = {"x-api-key": api_key}
    else:
        req_url = target_url
        req_headers = HEADERS

    # 遇到 409 并发限制时自动等待并重试
    for attempt in range(2):
        try:
            res = requests.get(req_url, headers=req_headers, timeout=30)

            # 触发 409 并发限制时，等待 4 秒后自动重试
            if res.status_code == 409 and attempt == 0:
                time.sleep(4)
                continue

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
                # 过滤“买/征/收”等求购帖，只保留卖家发出的出售贴
                if len(title) > 3 and not any(k in title for k in ["买", "徵", "征", "收"]):
                    href = item["href"]
                    if not href.startswith("http"):
                        href = "https://market.dcview.com" + href
                    content = f"标题: {title}\n链接: {href}"
                    content_hash = hashlib.md5(content.encode("utf-8")).hexdigest()
                    return content, content_hash

            return None, None

        except Exception as e:
            if attempt == 0:
                time.sleep(3)
                continue
            print(f"[DCView] 抓取网络异常 '{keyword}': {e}")
            return None, None

    return None, None
