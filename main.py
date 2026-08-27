import os
import json
import smtplib
import urllib.parse
from email.mime.text import MIMEText
from email.header import Header

# 导入 Threads 关键词抓取函数
from fetchers.threads import get_latest_keyword_post

# ================= 配置区域 =================
# 你想监控的多个相机关键词列表
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
    "Sony RX10m4"
]

# 保存所有关键词历史记录的文件（保持名称不变，无需修改 GitHub Actions 配置文件）
HISTORY_FILE = "threads_state.json"

# 邮箱配置
SMTP_SERVER = "smtp.qq.com"  # 若用 163 改为 smtp.163.com
SMTP_PORT = 465

SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "你的发件邮箱@qq.com")
SENDER_PASS = os.environ.get("SENDER_PASS", "你的邮箱授权码")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL", SENDER_EMAIL)


# ================= 辅助函数 =================
def load_all_states():
    """读取所有关键词的历史记录字典"""
    if not os.path.exists(HISTORY_FILE):
        return {}
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_all_states(states):
    """保存所有关键词的状态字典"""
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(states, f, ensure_ascii=False, indent=2)


def send_email(subject, body):
    """发送 HTML 邮件通知"""
    message = MIMEText(body, "html", "utf-8")
    message["From"] = Header(f"相机监控助手 <{SENDER_EMAIL}>", "utf-8")
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


# ================= 主流程 =================
def main():
    print(f"🔍 开始检查 {len(TARGET_KEYWORDS)} 个相机关键词的 Threads 更新...\n")
    
    all_states = load_all_states()
    updated_count = 0

    for keyword in TARGET_KEYWORDS:
        print(f"正在检查关键词:【{keyword}】...")
        content, content_hash = get_latest_keyword_post(keyword)
        
        if not content:
            print(f"  └─ ⚠️ 未能获取到【{keyword}】的相关帖文，跳过。")
            continue

        # 获取该关键词上一次记录的哈希值
        last_hash = all_states.get(keyword, {}).get("hash")

        if content_hash != last_hash:
            print(f"  └─ 🔔 检测到【{keyword}】有新帖文！正在发送邮件...")
            
            subject = f"🔔 Threads 出现相机关键词【{keyword}】的新帖文！"
            html_content = content.replace("\n", "<br>")
            
            # 拼接正确的搜索 URL
            encoded_kw = urllib.parse.quote(keyword)
            search_link = f"https://www.threads.net/search?q={encoded_kw}"

            body = f"""
            <h3>监控到相机关键词最新讨论：</h3>
            <p><b>关键词：</b> {keyword}</p>
            <p><b>搜索结果链接：</b> <a href="{search_link}">{search_link}</a></p>
            <hr>
            <h4>最新帖文摘要：</h4>
            <div style="background-color: #f5f5f5; padding: 15px; border-radius: 8px; font-size: 14px; line-height: 1.6;">
                {html_content}
            </div>
            """
            send_email(subject, body)
            
            # 更新该关键词的状态
            all_states[keyword] = {
                "hash": content_hash,
                "content": content
            }
            updated_count += 1
        else:
            print(f"  └─ ✅【{keyword}】内容无变化。")

    # 统一保存更新后的所有状态
    save_all_states(all_states)
    print(f"\n🎉 所有关键词巡检完毕，本次共有 {updated_count} 个关键词触发更新通知。")


if __name__ == "__main__":
    main()
