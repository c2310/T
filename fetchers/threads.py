import hashlib
import json
import re
import urllib.parse
import requests
from bs4 import BeautifulSoup


def get_latest_keyword_post(keyword):
    """抓取 Threads 指定关键词搜索结果中的最新贴文正文与 MD5 哈希值

    :param keyword: 搜索关键词（如 '人工智能' 或 'Python'）
    :return: (post_text, post_hash)
    """
    # 对关键词进行 URL 编码（处理中文或空格）
    encoded_keyword = urllib.parse.quote(keyword)
    url = f"https://www.threads.net/search?q={encoded_keyword}&serp_type=default"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        # 从搜索页面的 JSON 数据流中提取贴文正文
        post_text = _extract_from_embedded_json(response.text)

        if not post_text:
            print(f"[警告] 未能找到关于关键词 '{keyword}' 的相关帖文。")
            return None, None

        post_hash = hashlib.md5(post_text.encode("utf-8")).hexdigest()
        return post_text, post_hash

    except Exception as e:
        print(f"[Threads 关键词抓取异常] 关键词 '{keyword}': {e}")
        return None, None


def _extract_from_embedded_json(html):
    """从页面 JSON 数据中提取贴文正文"""
    try:
        scripts = re.findall(
            r'<script type="application/json"[^>]*>(.*?)</script>', html, re.DOTALL
        )
        for script in scripts:
            if '"text"' in script:
                matches = re.findall(r'"text"\s*:\s*"((?:[^"\\]|\\.)*)"', script)
                for match in matches:
                    text = match.encode("utf-8").decode("unicode_escape")
                    text = text.replace("\\n", "\n").replace('\\"', '"').strip()
                    # 过滤掉短词或 URL，提取有效帖文内容
                    if len(text) > 5 and not text.startswith("http"):
                        return text
    except Exception:
        pass
    return None
