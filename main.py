import json
import os
import smtplib
from email.header import Header
from email.mime.text import MIMEText

# 导入新的关键词抓取函数
from fetchers.threads import get_latest_keyword_post

# ================= 配置区域 =================
# 1. 填入你想监控的关键词（例如 "ChatGPT"、"股票" 或 "二手手机"）
TARGET_KEYWORD = "Python"

# 2. 保存历史记录的文件名（建议加上关键词区分）
HISTORY_FILE = f"threads_kw_{TARGET_KEYWORD}_state.json"

# 3. 邮箱配置
SMTP_SERVER = "smtp.qq.com"  # 若用 163 修改为 smtp.163.com
SMTP_PORT = 465

SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "你的发件邮箱@qq.com")
SENDER_PASS = os.environ.get("SENDER_PASS", "你的邮箱授权码")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL", SENDER_EMAIL)


# ================= 辅助函数 =================
def has_changed(new_hash):
    if not os.path.exists(HISTORY_FILE):
        return True
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("hash") != new_hash
    except Exception:
        return True


def save_state(content, content_hash):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {"hash": content_hash, "content": content},
            f,
            ensure_ascii=False,
            indent=2,
        )


def send_email(subject, body):
    message = MIMEText(body, "html", "utf-8")
    message["From"] = Header(f"Threads 关键词监控助手 <{SENDER_EMAIL}>", "utf-8")
    message["To"] = Header(RECEIVER_EMAIL, "utf-8")
    message["Subject"] = Header(subject, "utf-8")

    try:
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(SENDER_EMAIL, SENDER_PASS)
        server.sendmail(SENDER_EMAIL, [RECEIVER_EMAIL], message.as_string())
        server.quit()
        print("✅ 邮件发送成功！")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")


# ================= 主流程 =================
def main():
    print(f"🔍 开始检查 Threads 关于关键词【{TARGET_KEYWORD}】的最新更新...")

    content, content_hash = get_latest_keyword_post(TARGET_KEYWORD)

    if not content:
        print("⚠️ 未能获取到相关的搜索内容。")
        return

    if has_changed(content_hash):
        print("🔔 检测到关键词有新帖文！正在发送邮件通知...")
        subject = f"🔔 Threads 出现关于【{TARGET_KEYWORD}】的新帖文！"

        html_content = content.replace("\n", "<br>")
        search_link = f"https://www.threads.net/search?q={TARGET_KEYWORD}"

        body = f"""
        <h3>监控到关键词最新讨论：</h3>
        <p><b>关键词：</b> {TARGET_KEYWORD}</p>
        <p><b>搜索结果链接：</b> <a href="{search_link}">{search_link}</a></p>
        <hr>
        <h4>最新帖文摘要：</h4>
        <div style="background-color: #f5f5f5; padding: 15px; border-radius: 8px; font-size: 14px; line-height: 1.6;">
            {html_content}
        </div>
        """
        send_email(subject, body)
        save_state(content, content_hash)
    else:
        print("✅ 内容无变化，无需通知。")


if __name__ == "__main__":
    main()
