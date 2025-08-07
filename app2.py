from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import datetime
import requests

# Mapping of MLB team names to their traditional Chinese translations
TEAM_TRANSLATIONS = {
    "New York Yankees": "紐約洋基",
    "Boston Red Sox": "波士頓紅襪",
    "Toronto Blue Jays": "多倫多藍鳥",
    "Tampa Bay Rays": "坦帕灣光芒",
    "Baltimore Orioles": "巴爾的摩金鶯",
    "Cleveland Guardians": "克里夫蘭守護者",
    "Chicago White Sox": "芝加哥白襪",
    "Kansas City Royals": "堪薩斯城皇家",
    "Detroit Tigers": "底特律老虎",
    "Minnesota Twins": "明尼蘇達雙城",
    "Houston Astros": "休士頓太空人",
    "Texas Rangers": "德州遊騎兵",
    "Seattle Mariners": "西雅圖水手",
    "Los Angeles Angels": "洛杉磯天使",
    "Oakland Athletics": "奧克蘭運動家",
    "Atlanta Braves": "亞特蘭大勇士",
    "New York Mets": "紐約大都會",
    "Philadelphia Phillies": "費城費城人",
    "Washington Nationals": "華盛頓國民",
    "Miami Marlins": "邁阿密馬林魚",
    "Chicago Cubs": "芝加哥小熊",
    "Cincinnati Reds": "辛辛那提紅人",
    "Milwaukee Brewers": "密爾瓦基釀酒人",
    "St. Louis Cardinals": "聖路易紅雀",
    "Pittsburgh Pirates": "匹茲堡海盜",
    "Los Angeles Dodgers": "洛杉磯道奇",
    "San Diego Padres": "聖地牙哥教士",
    "San Francisco Giants": "舊金山巨人",
    "Arizona Diamondbacks": "亞利桑那響尾蛇",
    "Colorado Rockies": "科羅拉多洛磯",
}

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
    # Use simplified and traditional Chinese for tomorrow's schedule
    if user_msg in ["明日賽事", "明日赛事"]:
        # Determine the local "tomorrow" date (Asia/Taipei) and use it for both display and schedule lookup.
        # MLB schedules are organized by date, so the local calendar day should match the desired games.
        try:
            from zoneinfo import ZoneInfo
            now_local = datetime.datetime.now(ZoneInfo("Asia/Taipei"))
            tomorrow_local = now_local.date() + datetime.timedelta(days=1)
        except Exception:
            # Fallback: use system date when zoneinfo isn't available
            today = datetime.date.today()
            tomorrow_local = today + datetime.timedelta(days=1)
        # Format the date display (e.g., 8月8日)
        month_str = str(tomorrow_local.month)
        day_str = str(tomorrow_local.day)
        date_display = f"{month_str}月{day_str}日"
        try:
            # Fetch the schedule for the local tomorrow date
            url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={tomorrow_local.isoformat()}"
            res = requests.get(url)
            data = res.json()
            games = []
            dates = data.get('dates', [])
            if dates:
                games = dates[0].get('games', [])
            result_lines = []
            for game in games:
                away = game['teams']['away']['team']['name']
                home = game['teams']['home']['team']['name']
                # Translate team names
                away_cn = TEAM_TRANSLATIONS.get(away, away)
                home_cn = TEAM_TRANSLATIONS.get(home, home)
                away_score = game['teams']['away'].get('score')
                home_score = game['teams']['home'].get('score')
                if away_score is not None and home_score is not None:
                    # Show Chinese team names only with scores, no English names
                    line = f"{away_cn} vs {home_cn} {away_score}-{home_score}"
                else:
                    # No score yet; just show matchup without English names
                    line = f"{away_cn} vs {home_cn}"
                result_lines.append(line)
            if result_lines:
                # Use a simple divider line between each game for readability
                divider = "-----"
                reply = f"{date_display}賽事：\n" + f"\n{divider}\n".join(result_lines)
            else:
                reply = f"{date_display}沒有 MLB 賽事"
        except Exception:
            reply = "無法取得比賽資料，請稍後再試"
    else:
        reply = f"你輸入的是：{user_msg}"
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

if __name__ == "__main__":
    app.run()
