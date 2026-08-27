import hashlib
import re
import urllib.parse
import requests


def get_latest_keyword_post(keyword):
    """抓取 Threads 最新关键词贴文"""
    encoded_keyword = urllib.parse.quote(keyword)
    url = f"https://www.threads.net/search?q={encoded_keyword}&serp_type=default"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # 尝试正则提取嵌入在 HTML 中的 JSON 贴文正文
        scripts = re.findall(
            r'<script type="application/json"[^>]*>(.*?)</script>',
            response.text,
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
                        content = f"正文: {text}\n链接: {url}"
                        content_hash = hashlib.md5(
                            content.encode("utf-8")
                        ).hexdigest()
                        return content, content_hash

        return None, None
    except Exception as e:
        print(f"[Threads 抓取异常] 关键词 '{keyword}': {e}")
        return None, None
