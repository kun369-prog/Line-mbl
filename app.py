from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os

app = Flask(__name__)
line_bot_api = LineBotApi(os.environ.get("CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.environ.get("CHANNEL_SECRET"))

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        # Return OK even if signature is invalid to avoid 400 errors during webhook verification
        return 'OK'
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # Trim whitespace and newlines from the incoming message
    user_msg = event.message.text.strip()
    # Accept both traditional and simplified Chinese commands for today's game info
    if user_msg in ["今日賽事", "今日赛事"]:
        reply = "今天的 MLB 賽事有:\n1. 洋基 vs 紅襪\n2. 道奇 vs 響尾蛇"
    else:
        reply = f"你輸入的是：{user_msg}"
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

if __name__ == "__main__":
    app.run()
