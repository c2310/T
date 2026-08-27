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


def send_email(subject, body):
    message = MIMEText(body, "html", "utf-8")
    message["From"] = Header(f"多平台相机监控助手 <{SENDER_EMAIL}>", "utf-8")
    message["To"] = Header(RECEIVER_EMAIL, "utf-8")
    message["Subject"] = Header(subject, "utf-8")

    try:
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(SENDER_EMAIL, SENDER_PASS)
        server.sendmail(SENDER_EMAIL, [RECEIVER_EMAIL], message.as_string())
        server.quit()
        print(f"✅ 邮件发送成功: {subject}")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")


def check_platform(platform_name, fetch_func, all_states):
    updated_count = 0
    print(f"\n--- 🌐 开始巡检平台: 【{platform_name}】---")
    for keyword in TARGET_KEYWORDS:
        state_key = f"{platform_name}_{keyword}"
        content, content_hash = fetch_func(keyword)

        if not content:
            continue

        last_hash = all_states.get(state_key, {}).get("hash")
        if content_hash != last_hash:
            print(
                f"  └─ 🔔 【{platform_name}】检测到【{keyword}】有新动态！"
            )
            subject = f"🔔 [{platform_name}] 出现关键词【{keyword}】的新贴/出售！"

            html_content = content.replace("\n", "<br>")
            body = f"""
            <h3>[{platform_name}] 监控到相机最新讨论/出售：</h3>
            <p><b>关键词：</b> {keyword}</p>
            <p><b>来源平台：</b> {platform_name}</p>
            <hr>
            <h4>帖文/商品摘要：</h4>
            <div style="background-color: #f5f5f5; padding: 15px; border-radius: 8px; font-size: 14px; line-height: 1.6;">
                {html_content}
            </div>
            """
            send_email(subject, body)
            all_states[state_key] = {"hash": content_hash, "content": content}
            updated_count += 1
        else:
            print(f"  └─ ✅ 【{platform_name}】:【{keyword}】无变化。")
    return updated_count


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--all"
    all_states = load_all_states()
    total_updates = 0

    # 5分钟高频组：DCView、PTT
    if mode in ["--fast", "--all"]:
        total_updates += check_platform(
            "DCView", get_latest_dcview_post, all_states
        )
        total_updates += check_platform(
            "PTT_DC_SALE", get_latest_ptt_post, all_states
        )

    # 15分钟常规组：Threads、Yahoo拍卖
    if mode in ["--threads", "--slow", "--all"]:
        total_updates += check_platform(
            "Threads", get_threads_post, all_states
        )
        total_updates += check_platform(
            "Yahoo拍卖", get_latest_yahoo_post, all_states
        )

    save_all_states(all_states)
    print(
        f"\n🎉 巡检完毕，本次共发送 {total_updates} 封新通知邮件。"
    )


if __name__ == "__main__":
    main()
