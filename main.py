import json
import os
import sys
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

from fetchers.dcview import get_latest_dcview_post
from fetchers.ptt import get_latest_ptt_post
from fetchers.threads import get_latest_keyword_post as get_threads_post
from fetchers.yahoo import get_latest_yahoo_post

# 全局关键词配置
TARGET_KEYWORDS = [
    "Canon G12",
    "Canon G15",
    "Canon G16",
    "Canon G11",
    "Canon G10",
    "Canon S95",
    "Canon Sx70hs",
    "Canon G",
    "Sony Rx10iv",
    "Sony RX10m4",
    "Ricoh GR",
    "Canon G7x",
]

HISTORY_FILE = "threads_state.json"

# 从 GitHub Secrets / 环境变量中读取 Discord Webhook URL
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")


def load_all_states():
    if not os.path.exists(HISTORY_FILE):
        return {}
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_all_states(states):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(states, f, ensure_ascii=False, indent=2)


def send_discord_notify(notifications):
    if not notifications:
        print("ℹ️ 本次没有新贴文，跳过 Discord 推送。")
        return

    if not DISCORD_WEBHOOK_URL:
        print("❌ 错误：未配置 DISCORD_WEBHOOK_URL 环境变量！")
        return

    embeds = []
    for item in notifications:
        clean_content = item["content"][:500]
        embeds.append(
            {
                "title": f"🔔 [{item['platform']}] 检测到新动态：{item['keyword']}",
                "description": clean_content,
                "color": 3447003,  # 蓝色边框 (#3498DB)
                "footer": {"text": "多平台二手相机监控助手"},
            }
        )

    chunk_size = 10
    for i in range(0, len(embeds), chunk_size):
        chunk = embeds[i : i + chunk_size]
        payload = {
            "username": "二手相机监控助手",
            "avatar_url": "https://cdn-icons-png.flaticon.com/512/2950/2950687.png",
            "embeds": chunk,
        }

        try:
            resp = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
            if resp.status_code in [200, 204]:
                print(f"  ✅ Discord 推送成功！已发送 {len(chunk)} 条动态。")
            else:
                print(
                    f"❌ Discord 推送失败，状态码: {resp.status_code}, 返回信息: {resp.text}"
                )
        except Exception as e:
            print(f"❌ Discord 请求发送异常: {e}")


def worker_fetch(platform_name, fetch_func, keyword):
    """单任务 Worker，保证安全捕获异常"""
    try:
        content, content_hash = fetch_func(keyword)
        return keyword, content, content_hash
    except Exception as e:
        print(f"  ❌ 【{platform_name}】：【{keyword}】 抓取过程报错: {e}")
        return keyword, None, None


def check_platform(platform_name, fetch_func, all_states, notifications):
    print(f"\n--- 🌐 开始巡检平台：【{platform_name}】 ---")

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(worker_fetch, platform_name, fetch_func, kw): kw
            for kw in TARGET_KEYWORDS
        }

        for future in as_completed(futures):
            try:
                keyword, content, content_hash = future.result()
            except Exception as e:
                print(f"  ❌ 提取结果失败: {e}")
                continue

            state_key = f"{platform_name}_{keyword}"

            if not content:
                print(
                    f"  ⚠️ 【{platform_name}】：【{keyword}】 未能获取到有效数据。"
                )
                continue

            last_hash = all_states.get(state_key, {}).get("hash")
            if content_hash != last_hash:
                print(f"  🔔 【{platform_name}】检测到 【{keyword}】 有新动态！")
                notifications.append(
                    {
                        "platform": platform_name,
                        "keyword": keyword,
                        "content": content,
                    }
                )
                all_states[state_key] = {"hash": content_hash}
            else:
                print(f"  └─ 【{platform_name}】：【{keyword}】 无变化。")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--all"
    all_states = load_all_states()
    notifications = []

    if mode in ["--fast", "--all"]:
        check_platform(
            "DCView", get_latest_dcview_post, all_states, notifications
        )
        check_platform(
            "PTT_DC_SALE", get_latest_ptt_post, all_states, notifications
        )

    if mode in ["--threads", "--slow", "--all"]:
        check_platform("Threads", get_threads_post, all_states, notifications)
        check_platform(
            "Yahoo", get_latest_yahoo_post, all_states, notifications
        )

    if notifications:
        send_discord_notify(notifications)
    else:
        print("\nℹ️ 巡检完毕：数据没有变动，不触发 Discord 发送。")

    save_all_states(all_states)
    print(f"\n🎉 巡检完毕，本次共收集到 {len(notifications)} 条新动态。")


if __name__ == "__main__":
    main()
