import hashlib
import json
import re
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
import requests


def _fetch_single_keyword(keyword):
    """单条关键词抓取逻辑（缩短超时时间至 8 秒）"""
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
        response = requests.get(url, headers=headers, timeout=8)
        response.raise_for_status()

        post_text = _extract_from_embedded_json(response.text)
        if not post_text:
            return keyword, None, None

        post_hash = hashlib.md5(post_text.encode("utf-8")).hexdigest()
        return keyword, post_text, post_hash
    except Exception as e:
        print(f"[Threads 抓取超时/异常] 关键词 '{keyword}': {e}")
        return keyword, None, None


def get_latest_keyword_post(keyword):
    """保持向后兼容的单条抓取入口"""
    _, text, post_hash = _fetch_single_keyword(keyword)
    return text, post_hash


def _extract_from_embedded_json(html):
    """从页面 JSON 数据中提取贴文正文"""
    try:
        scripts = re.findall(
            r'<script type="application/json"[^>]*>(.*?)</script>',
            html,
            re.DOTALL,
        )
        for script in scripts:
            if '"text"' in script:
                matches = re.findall(
                    r'"text"\s*:\s*"((?:[^"\\]|\\.)*)"', script
                )
                for match in matches:
                    text = match.encode("utf-8").decode("unicode_escape")
                    text = text.replace("\\n", "\n").replace('\\"', '"').strip()
                    if len(text) > 5 and not text.startswith("http"):
                        return text
    except Exception:
        pass
    return None
