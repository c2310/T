import json
import os
import smtplib
import sys
from email.header import Header
from email.mime.text import MIMEText

from fetchers.dcview import get_latest_dcview_post
from fetchers.ptt import get_latest_ptt_post
from fetchers.threads import get_latest_keyword_post as get_threads_post
from fetchers.yahoo import get_latest_yahoo_post

# ================= 全局关键词配置 =================
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

SMTP_SERVER = "smtp.qq.com"  # 163邮箱修改为 smtp.163.com
SMTP_PORT = 465

SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "你的发件邮箱@qq.com")
SENDER_PASS = os.environ.get("SENDER_PASS", "你的邮箱授权码")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL", SENDER_EMAIL)


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


def send_batch_email(notifications):
    """将所有新动态打包在一封邮件中发送"""
    if not notifications:
        return

    subject = f"🔔 [二手相机监控] 检测到 {len(notifications)} 条新动态！"

    body_items = ""
    for item in notifications:
        html_content = item["content"].replace("\n", "<br>")
        body_items += f"""
        <div style="background-color: #f8f9fa; border-left: 4px solid #007bff; padding: 12px; margin-bottom: 15px;">
            <p style="margin: 0 0 5px 0;"><b>平台：</b> {item['platform']} | <b>关键词：</b> <span style="color: #d9534f;">{item['keyword']}</span></p>
            <div style="font-size: 14px; color: #333; line-height: 1.5;">{html_content}</div>
        </div>
        """

    body = f"""
    <h2>📸 相机二手市场最新动态汇总</h2>
    <p>本次巡检共搜集到 {len(notifications)} 个最新讨论/出售信息：</p>
    <hr>
    {body_items}
    """

    message = MIMEText(body, "html", "utf-8")
    message["From"] = Header(f"多平台相机监控助手 <{SENDER_EMAIL}>", "utf-8")
    message["To"] = Header(RECEIVER_EMAIL, "utf-8")
    message["Subject"] = Header(subject, "utf-8")

    try:
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(SENDER_EMAIL, SENDER_PASS)
        server.sendmail(SENDER_EMAIL, [RECEIVER_EMAIL], message.as_string())
        server.quit()
        print(
            f"✅ 汇总邮件发送成功！包含 {len(notifications)} 条新动态。"
        )
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")


def check_platform(platform_name, fetch_func, all_states, notifications):
    print(f"\n--- 🌐 开始巡检平台: 【{platform_name}】---")
    for keyword in TARGET_KEYWORDS:
        state_key = f"{platform_name}_{keyword}"
        content, content_hash = fetch_func(keyword)

        if not content:
            print(
                f"  └─ ⚠️ 【{platform_name}】:【{keyword}】未能获取到有效数据（可能被拦截）。"
            )
            continue

        last_hash = all_states.get(state_key, {}).get("hash")
        if content_hash != last_hash:
            print(
                f"  └─ 🔔 【{platform_name}】检测到【{keyword}】有新动态！"
            )
            notifications.append(
                {
                    "platform": platform_name,
                    "keyword": keyword,
                    "content": content,
                }
            )
            all_states[state_key] = {"hash": content_hash, "content": content}
        else:
            print(f"  └─ ✅ 【{platform_name}】:【{keyword}】无变化。")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--all"
    all_states = load_all_states()
    notifications = []

    # 5分钟高频组：DCView、PTT
    if mode in ["--fast", "--all"]:
        check_platform(
            "DCView", get_latest_dcview_post, all_states, notifications
        )
        check_platform(
            "PTT_DC_SALE", get_latest_ptt_post, all_states, notifications
        )

    # 15分钟常规组：Threads、Yahoo
    if mode in ["--threads", "--slow", "--all"]:
        check_platform(
            "Threads", get_threads_post, all_states, notifications
        )
        check_platform(
            "Yahoo", get_latest_yahoo_post, all_states, notifications
        )

    # 发送汇总邮件
    if notifications:
        send_batch_email(notifications)

    save_all_states(all_states)
    print(
        f"\n🎉 巡检完毕，本次共收集到 {len(notifications)} 条新动态。"
    )


if __name__ == "__main__":
    main()
