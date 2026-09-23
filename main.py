import json
import os
import sys
import time
import requests

from fetchers.dcview import get_latest_dcview_post
from fetchers.ptt import get_latest_ptt_post
from fetchers.threads import get_latest_keyword_post as get_threads_post
from fetchers.yahoo import get_latest_yahoo_post

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
                "color": 3447003,
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


def check_platform(platform_name, fetch_func, all_states, notifications):
    print(f"\n--- 🌐 开始巡检平台：【{platform_name}】 ---")

    # ⚠️ 废除 ThreadPoolExecutor，使用绝对严格的串行循环，防止 ScrapingAnt 报并发 409
    for keyword in TARGET_KEYWORDS:
        try:
            content, content_hash = fetch_func(keyword)
            state_key = f"{platform_name}_{keyword}"

            if not content:
                print(f"  ⚠️ 【{platform_name}】：【{keyword}】 未能获取到有效数据。")
            else:
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
            
            # ⚠️ 每次请求间预留 2.5 秒缓冲，确保 ScrapingAnt 完全释放连接
            time.sleep(3.5)

        except Exception as e:
            print(f"  ❌ 【{platform_name}】：【{keyword}】 抓取过程报错: {e}")


def main():
    ant_key = os.environ.get("SCRAPINGANT_API_KEY")
    scraper_key = os.environ.get("SCRAPER_API_KEY")
    print(f"🔍 环境变量检查: SCRAPINGANT_API_KEY 长度 = {len(ant_key) if ant_key else 0}")
    print(f"🔍 环境变量检查: SCRAPER_API_KEY 长度 = {len(scraper_key) if scraper_key else 0}")

    mode = sys.argv[1] if len(sys.argv) > 1 else "--all"
    all_states = load_all_states()
    notifications = []

    if mode in ["--fast", "--all"]:
        check_platform("DCView", get_latest_dcview_post, all_states, notifications)
        check_platform("PTT_DC_SALE", get_latest_ptt_post, all_states, notifications)

    if mode in ["--threads", "--slow", "--all"]:
        check_platform("Threads", get_threads_post, all_states, notifications)
        check_platform("Yahoo", get_latest_yahoo_post, all_states, notifications)

    if notifications:
        send_discord_notify(notifications)
    else:
        print("\nℹ️ 巡检完毕：数据没有变动，不触发 Discord 发送。")

    save_all_states(all_states)
    print(f"\n🎉 巡检完毕，本次共收集到 {len(notifications)} 条新动态。")


if __name__ == "__main__":
    main()
