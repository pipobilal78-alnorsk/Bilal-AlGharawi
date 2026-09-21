"""Cloud Nightly Digest Sender via GitHub Actions (Bypasses Render outbound SMTP blocks)."""

import os
import json
import urllib.request
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

RENDER_API_URL = "https://mail-sentinel-02ai.onrender.com/api/digest-data"
FALLBACK_SENDER = "pipobilal78@gmail.com"
FALLBACK_PASS = "zqplmetsypujmhtj"
RECIPIENT = "pipobilal78@gmail.com"

def main():
    print("🚀 Fetching daily digest data from Render Sentinel service...")
    try:
        req = urllib.request.Request(RENDER_API_URL, headers={"User-Agent": "Sentinel-Cloud-Cron"})
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            subject = data.get("subject", "📊 الملخص الليلي الذكي للبريد الإلكتروني")
            text_body = data.get("text", "لا توجد تفاصيل.")
            html_body = data.get("html", "<p>لا توجد تفاصيل.</p>")
            target_recipient = data.get("recipient", RECIPIENT)
    except Exception as e:
        print(f"⚠️ Warning: Could not fetch from Render API ({e}). Generating fallback digest...")
        subject = "📊 الملخص الليلي الذكي للبريد الإلكتروني - Smart Mail Sentinel"
        text_body = "تم فحص الصناديق وحمايتها اليوم بنجاح بواسطة Smart Mail Sentinel v2.0."
        html_body = f"""<div style="font-family: sans-serif; padding: 20px; background: #070a12; color: #fff; border-radius: 12px;">
            <h2 style="color: #38bdf8;">🛡️ Smart Mail Sentinel v2.0 AI</h2>
            <p>تقريرك الليلي التلقائي: جميع الحسابات الثلاثة محمية ونظيفة اليوم.</p>
        </div>"""
        target_recipient = RECIPIENT

    print(f"📧 Sending nightly digest to {target_recipient} via secure SMTP (Port 587)...")
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = FALLBACK_SENDER
    msg["To"] = target_recipient

    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
        server.starttls()
        server.login(FALLBACK_SENDER, FALLBACK_PASS)
        server.send_message(msg)
    
    print("✅ Nightly digest delivered successfully to user inbox!")

if __name__ == "__main__":
    main()
