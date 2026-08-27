import hashlib
import json
import re
import urllib.parse
import requests


def get_latest_keyword_post(keyword):
    """抓取 Threads 最新关键词贴文（伪装官方 Web App）"""
    encoded_keyword = urllib.parse.quote(keyword)
    url = f"https://www.threads.net/search?q={encoded_keyword}&serp_type=default"

    # 深度伪装为 Threads 网页客户端
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        ),
        "Accept": "*/*",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "X-IG-App-ID": "238260118697367",  # Threads 官方 Web 端 App ID
        "Referer": f"https://www.threads.net/search?q={encoded_keyword}",
    }

    try:
        response = requests.get(url, headers=headers, timeout=12)
        if response.status_code != 200:
            return None, None

        # 尝试从页面嵌入的 JSON 数据中提取正文
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
                        text = json.loads(f'"{match}"').strip()
                    except Exception:
                        text = (
                            match.encode("utf-8", "ignore")
                            .decode("utf-8", "ignore")
                            .strip()
                        )

                    # 过滤无效或太短的内容
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
