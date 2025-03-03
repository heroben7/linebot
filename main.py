import os
import datetime
from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, ImageMessage, TextSendMessage
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# ดึงค่าจาก Environment Variables
LINE_BOT_API = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
HANDLER = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
line_bot_api = LineBotApi(LINE_BOT_API)

# ตัวแปรเก็บจำนวนรูปภาพของสมาชิก
user_image_count = {}

# เวลาที่ต้องการนับ (09:00 - 20:00)
START_TIME = 9
END_TIME = 20

@app.route("/callback", methods=["POST"])
def callback():
    """ รับ Webhook Event จาก LINE """
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        HANDLER.handle(body, signature)
    except Exception as e:
        print(e)
        return "Error", 400

    return "OK", 200

@HANDLER.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    """ นับจำนวนรูปภาพของสมาชิก """
    global user_image_count
    now = datetime.datetime.now()

    if START_TIME <= now.hour < END_TIME:
        user_id = event.source.user_id
        user_image_count[user_id] = user_image_count.get(user_id, 0) + 1

        reply_text = f"📸 คุณส่งรูปมาแล้ว {user_image_count[user_id]} รูปวันนี้!"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

def reset_and_report():
    """ ส่งรายงานเวลา 20:00 น. และรีเซ็ตค่า """
    global user_image_count
    summary = "📊 **สรุปจำนวนรูปที่ส่งวันนี้**\n"

    if user_image_count:
        for user_id, count in user_image_count.items():
            summary += f"- {user_id[:6]}***: {count} รูป\n"
    else:
        summary = "📊 วันนี้ยังไม่มีใครส่งรูปเลย!"

    GROUP_ID = "YOUR_GROUP_ID"
    line_bot_api.push_message(GROUP_ID, TextSendMessage(text=summary))

    user_image_count = {}

# ตั้งเวลาส่งสรุปทุกวันตอน 20:00 น.
scheduler = BackgroundScheduler()
scheduler.add_job(reset_and_report, "cron", hour=20, minute=0)
scheduler.start()

if __name__ == "__main__":
    app.run(port=5000)
