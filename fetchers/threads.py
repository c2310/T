import hashlib
import json
import re
import requests
from bs4 import BeautifulSoup


def get_latest_post(username):
    """抓取 Threads 指定用户的最新公开贴文内容与 MD5 哈希值

    :param username: Threads 用户名（不带 @，如 'zuck'）
    :return: (post_text, post_hash)
    """
    username = username.lstrip("@")
    url = f"https://www.threads.net/@{username}"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Sec-Fetch-Site": "same-origin",
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        # 1. 优先尝试从内嵌的 JSON 数据流中精确匹配贴文
        post_text = _extract_from_embedded_json(response.text)

        # 2. 兜底方案：从 Open Graph 标签提取
        if not post_text:
            post_text = _extract_from_meta_tags(response.text)

        if not post_text:
            print(f"[警告] 未能提取到 @{username} 的内容，账号可能为私密或无贴文。")
            return None, None

        # 计算内容的哈希值用于比对更新
        post_hash = hashlib.md5(post_text.encode("utf-8")).hexdigest()
        return post_text, post_hash

    except Exception as e:
        print(f"[Threads 抓取异常] 用户 @{username}: {e}")
        return None, None


def _extract_from_embedded_json(html):
    """提取页面内嵌 JSON 脚本中的最新贴文正文"""
    try:
        # Threads 页面会在 script 标签里序列化返回帖文 JSON 数据
        scripts = re.findall(
            r'<script type="application/json"[^>]*>(.*?)</script>', html, re.DOTALL
        )
        for script in scripts:
            if '"caption"' in script or '"thread_items"' in script:
                # 匹配 json 中的 text 字段
                matches = re.findall(r'"text"\s*:\s*"((?:[^"\\]|\\.)*)"', script)
                for match in matches:
                    # 过滤掉头像描述或系统通用短语，匹配有效长贴文
                    text = match.encode("utf-8").decode("unicode_escape")
                    text = text.replace("\\n", "\n").replace('\\"', '"').strip()
                    if len(text) > 2 and not text.startswith("http"):
                        return text
    except Exception:
        pass
    return None


def _extract_from_meta_tags(html):
    """从页面 og:description 元标签中提取（通常包含最新发布的片段）"""
    soup = BeautifulSoup(html, "html.parser")
    meta = soup.find("meta", property="og:description") or soup.find(
        "meta", attrs={"name": "description"}
    )
    if meta and meta.get("content"):
        return meta["content"].strip()
    return None


# ================= 本地单独测试代码 =================
if __name__ == "__main__":
    test_user = "zuck"  # 替换为想测试的 Threads 用户名
    print(f"正在测试抓取 Threads 用户: @{test_user} ...")
    content, content_hash = get_latest_post(test_user)

    if content:
        print("\n=== 抓取成功 ===")
        print(f"最新贴文内容:\n{content}")
        print(f"内容 Hash 值: {content_hash}")
    else:
        print("\n=== 抓取失败 ===")
