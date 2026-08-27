import os
import json
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# 导入你刚刚在 fetchers 文件夹里写的 Threads 抓取模块
from fetchers.threads import get_latest_post

# ================= 配置区域 =================
# 1. 想监控的 Threads 用户名（不带 @，例如扎克伯格的账号是 zuck）
TARGET_USER = "zuck"

# 2. 保存历史抓取记录的文件名
HISTORY_FILE = "threads_state.json"

# 3. 邮箱发送配置（以 QQ 邮箱为例，网易邮箱填 smtp.163.com，Gmail 填 smtp.gmail.com）
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 465

# 优先从环境变量读取邮箱和授权码（安全防泄露），读取不到时使用默认值
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "你的发件邮箱@qq.com")
SENDER_PASS = os.environ.get("SENDER_PASS", "你的邮箱授权码")
# 接收通知的邮箱，默认发送给自己
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL", SENDER_EMAIL)


# ================= 辅助函数 =================
def has_changed(new_hash):
    """检查内容是否发生了变化"""
    if not os.path.exists(HISTORY_FILE):
        return True
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("hash") != new_hash
    except Exception:
        return True


def save_state(content, content_hash):
    """保存最新状态到 JSON 文件"""
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump({"hash": content_hash, "content": content}, f, ensure_ascii=False, indent=2)


def send_email(subject, body):
    """发送 HTML 邮件通知"""
    message = MIMEText(body, "html", "utf-8")
    message["From"] = Header(f"Threads 监控助手 <{SENDER_EMAIL}>", "utf-8")
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
    print(f"🔍 开始检查 Threads 用户 @{TARGET_USER} 的最新更新...")
    
    # 调用 Threads 模块抓取最新动态
    content, content_hash = get_latest_post(TARGET_USER)
    
    if not content:
        print("⚠️ 未能获取到内容，可能是网络问题或目标账号无动态。")
        return

    # 比对历史记录
    if has_changed(content_hash):
        print("🔔 检测到 Threads 有新动态！正在发送邮件通知...")
        subject = f"🔔 Threads 用户 @{TARGET_USER} 发发布了新动态！"
        body = f"""
        <h3>监控到 Threads 新动态：</h3>
        <p><b>用户：</b> @{TARGET_USER}</p>
        <p><b>主页链接：</b> <a href="https://www.threads.net/@{TARGET_USER}">https://www.threads.net/@{TARGET_USER}</a></p>
        <hr>
        <h4>贴文最新内容：</h4>
        <div style="background-color: #f5f5f5; padding: 15px; border-radius: 8px; font-size: 14px; line-height: 1.6;">
            {content.replace('\n', '<br>')}
        </div>
        """
        send_email(subject, body)
        save_state(content, content_hash)
    else:
        print("✅ 内容无变化，无需通知。")

if __name__ == "__main__":
    main()
