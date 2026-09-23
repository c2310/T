import hashlib
import json
import os
import re
import urllib.parse
import requests


def is_chinese_text(text):
    return bool(re.search(r"[\u4e00-\u9fa5]", text))


def get_latest_keyword_post(keyword):
    encoded_keyword = urllib.parse.quote(keyword)
    target_url = f"https://www.threads.net/search?q={encoded_keyword}&serp_type=default&hl=zh-tw"

    api_key = os.environ.get("SCRAPINGANT_API_KEY") or os.environ.get("SCRAPER_API_KEY")
    
    if api_key:
        req_url = (
            f"https://api.scrapingant.com/v2/general"
            f"?url={urllib.parse.quote(target_url, safe='')}"
            f"&browser=false"
        )
        headers = {"x-api-key": api_key}
    else:
        req_url = target_url
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
            ),
            "Accept": "*/*",
            "Accept-Language": "zh-TW,zh;q=0.9,zh-CN;q=0.8,en-US;q=0.7",
            "X-IG-App-ID": "238260118697367",
        }

    try:
        response = requests.get(req_url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"[Threads 响应异常] 关键词: {keyword} | 状态码: {response.status_code} | 返回信息: {response.text[:150]}")
            return None, None

        if api_key:
            try:
                raw_text = response.json().get("content", "")
            except Exception:
                raw_text = response.text
        else:
            raw_text = response.text

        post_code_match = re.search(r'"code"\s*:\s*"([A-Za-z0-9_-]{10,12})"', raw_text)
        if post_code_match:
            post_shortcode = post_code_match.group(1)
            direct_post_url = f"https://www.threads.net/@/post/{post_shortcode}"
        else:
            direct_post_url = target_url

        scripts = re.findall(
            r'<script type="application/json"[^>]*>(.*?)</script>',
            raw_text,
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

                    if len(text) > 5 and not text.startswith("http") and is_chinese_text(text):
                        content = f"正文: {text}\n贴文链接: {direct_post_url}"
                        content_hash = hashlib.md5(
                            content.encode("utf-8")
                        ).hexdigest()
                        return content, content_hash

        return None, None
    except Exception as e:
        print(f"[Threads 抓取异常] 关键词 '{keyword}': {e}")
        return None, None
