import hashlib
import json
import re
import urllib.parse
import requests


def get_latest_keyword_post(keyword):
    """抓取 Threads 最新关键词贴文（兼容 Emoji 表情）"""
    encoded_keyword = urllib.parse.quote(keyword)
    url = f"https://www.threads.net/search?q={encoded_keyword}&serp_type=default"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

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
                    try:
                        # 使用 json.loads 安全解析带 Unicode/Emoji 的字符串
                        text = json.loads(f'"{match}"').strip()
                    except Exception:
                        text = (
                            match.encode("utf-8", "ignore")
                            .decode("utf-8", "ignore")
                            .strip()
                        )

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
