import hashlib
import json
import os
import re
import urllib.parse
import requests


def get_latest_keyword_post(keyword):
    """抓取 Threads 最新关键词贴文（支持 ScraperAPI 代理）"""
    encoded_keyword = urllib.parse.quote(keyword)
    target_url = f"https://www.threads.net/search?q={encoded_keyword}&serp_type=default"

    api_key = os.environ.get("SCRAPER_API_KEY")
    if api_key:
        req_url = f"http://api.scraperapi.com?api_key={api_key}&url={urllib.parse.quote(target_url)}&render=true"
    else:
        req_url = target_url

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        ),
        "Accept": "*/*",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "X-IG-App-ID": "238260118697367",
    }

    try:
        response = requests.get(req_url, headers=headers, timeout=25)
        if response.status_code != 200:
            return None, None

        scripts = re.findall(
            r'<script type="application/json"[^>]*>(.*?)</script>',
            response.text,
            re.DOTALL,
        )
        for script in scripts:
            if '"text"' in script:
                matches = re.findall(r'"text"\s*:\s*"((?:[^"\\]|\\.)*)"', script)
                for match in matches:
                    try:
                        text = json.loads(f'"{match}"').strip()
                    except Exception:
                        text = (
                            match.encode("utf-8", "ignore")
                            .decode("utf-8", "ignore")
                            .strip()
                        )

                    if len(text) > 5 and not text.startswith("http"):
                        content = f"正文: {text}\n链接: {target_url}"
                        content_hash = hashlib.md5(content.encode("utf-8")).hexdigest()
                        return content, content_hash

        return None, None
    except Exception as e:
        print(f"[Threads 抓取异常] 关键词 '{keyword}': {e}")
        return None, None
