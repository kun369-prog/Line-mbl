from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import datetime
import requests

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
        # Return OK even if signature is invalid to avoid errors during webhook verification
        return 'OK'
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_msg = event.message.text.strip()
    if user_msg in ["今日賽事", "今日赛事"]:
        # Fetch today's games and scores from MLB Stats API
        today = datetime.date.today().isoformat()
        try:
            url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}"
            res = requests.get(url)
            data = res.json()
            games = data.get('dates', [])
            if games:
                games = games[0].get('games', [])
            result_lines = []
            for game in games:
                away_team = game['teams']['away']['team']['name']
                home_team = game['teams']['home']['team']['name']
                away_score = game['teams']['away'].get('score')
                home_score = game['teams']['home'].get('score')
                if away_score is not None and home_score is not None:
                    result_lines.append(f"{away_team} {away_score} - {home_team} {home_score}")
                else:
                    result_lines.append(f"{away_team} vs {home_team}")
            if result_lines:
                reply = "今日賽事比分：\n" + "\n".join(result_lines)
            else:
                reply = "今天沒有 MLB 賽事"
        except Exception as e:
            reply = "無法取得今日賽事，請稍後再試"
    else:
        reply = f"你輸入的是：{user_msg}"
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

if __name__ == "__main__":
    app.run()
