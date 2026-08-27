import hashlib
import urllib.parse
import requests
from bs4 import BeautifulSoup


def get_latest_yahoo_post(keyword):
    """抓取 Yahoo拍卖 最新出售商品"""
    encoded_kw = urllib.parse.quote(keyword)
    # 按最新上架倒序排列
    url = f"https://tw.bid.yahoo.com/search/auction/product?p={encoded_kw}&sort=-etime"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
        )
    }

    try:
        response = requests.get(url, headers=headers, timeout=12)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # 匹配商品链接
        links = soup.find_all("a", href=lambda h: h and "/item/" in h)
        for link in links:
            title = link.get_text(strip=True)
            href = link["href"]
            if len(title) > 3:
                if not href.startswith("http"):
                    href = (
                        "https:" + href
                        if href.startswith("//")
                        else "https://tw.bid.yahoo.com" + href
                    )
                content = f"标题: {title}\n链接: {href}"
                content_hash = hashlib.md5(content.encode("utf-8")).hexdigest()
                return content, content_hash

        return None, None
    except Exception as e:
        print(f"[Yahoo拍卖 抓取异常] 关键词 '{keyword}': {e}")
        return None, None
