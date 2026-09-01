import hashlib
import urllib.parse
import requests
from bs4 import BeautifulSoup


def get_latest_dcview_post(keyword):
    """抓取 DCView 二手相机最新贴文"""
    encoded_kw = urllib.parse.quote(keyword)
    url = f"https://market.dcview.com/search/{encoded_kw}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            # 兼容多种标签匹配
            items = soup.find_all("a", href=lambda h: h and "/post/" in h)

            for item in items:
                title = item.get_text(strip=True)
                if len(title) > 3 and "买" not in title and "征" not in title:  # 过滤征求帖
                    href = item["href"]
                    if not href.startswith("http"):
                        href = "https://market.dcview.com" + href
                    content = f"标题: {title}\n链接: {href}"
                    content_hash = hashlib.md5(
                        content.encode("utf-8")
                    ).hexdigest()
                    return content, content_hash
        return None, None
    except Exception as e:
        print(f"[DCView 抓取异常] 关键词 '{keyword}': {e}")
        return None, None
