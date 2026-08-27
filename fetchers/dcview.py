import hashlib
import urllib.parse
import requests
from bs4 import BeautifulSoup


def get_latest_dcview_post(keyword):
    """抓取 DCView 二手相机市场最新贴文"""
    encoded_kw = urllib.parse.quote(keyword)
    url = f"http://market.dcview.com/search?keyword={encoded_kw}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
    }

    try:
        response = requests.get(url, headers=headers, timeout=12)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # 尝试匹配商品列表项
        items = (
            soup.select(".media")
            or soup.select(".list-group-item")
            or soup.select("article")
        )
        if not items:
            links = soup.find_all("a", href=lambda h: h and "/post/" in h)
            if links:
                title = links[0].text.strip()
                href = (
                    "http://market.dcview.com" + links[0]["href"]
                    if links[0]["href"].startswith("/")
                    else links[0]["href"]
                )
                content = f"标题: {title}\n链接: {href}"
                return content, hashlib.md5(content.encode("utf-8")).hexdigest()
            return None, None

        first_item = items[0]
        title = first_item.get_text(strip=True)
        a_tag = first_item.find("a")
        link = (
            a_tag["href"]
            if a_tag and "href" in a_tag.attrs
            else f"http://market.dcview.com/search?keyword={encoded_kw}"
        )
        if link.startswith("/"):
            link = "http://market.dcview.com" + link

        content = f"标题: {title}\n链接: {link}"
        content_hash = hashlib.md5(content.encode("utf-8")).hexdigest()
        return content, content_hash
    except Exception as e:
        print(f"[DCView 抓取异常] 关键词 '{keyword}': {e}")
        return None, None
