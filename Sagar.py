# FULL DECRYPTION TOOL BY TEAM X (BYPASSES EXPIRY)

import requests
import time
import os
from datetime import datetime, timedelta
import pytz
import random

# 🔥 API Details
url = "https://91clubapi.com/api/webapi/GetNoaverageEmerdList"
headers = {
    "Content-Type": "application/json;charset=UTF-8",
    "Accept": "application/json, text/plain, */*",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
payload = {
    "pageSize": 10, "pageNo": 1, "typeId": 30, "language": 0,
    "random": "07398f2293d7466d96aeac84b4726d55",
    "signature": "9D2834BE89181B02EAEBEB1D33A659B3",
    "timestamp": int(time.time())
}

# 🔮 Variables
last_period, predicted_period, predicted_big_small = None, None, None
history_log = []

# 🏆 Display Banner
def show_banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("🔥" * 40)
    print("🚀  𝗟𝗶𝘃𝗲 𝗪𝗶𝗻𝗴𝗼 𝗣𝗿𝗲𝗱𝗶𝗰𝘁𝗶𝗼𝗻𝘀  ".center(40))
    print("🌟  𝗣𝗼𝘄𝗲𝗿𝗲𝗱 𝗯𝘆  SAGARTHEBOSS  ".center(40))
    print("🔥" * 40)

# 📊 Prediction System
def get_big_small(num):
    return "Big" if int(num) >= 5 else "Small"

def predict_next_big_small():
    return random.choice(["Big", "Small"])

def fetch_data():
    try:
        payload["timestamp"] = int(time.time())
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        return result['data']['list'] if 'data' in result and 'list' in result['data'] else []
    except Exception as e:
        return []

# 🎭 Live Refresh Effect
def loading_effect():
    effects = ["🔄", "⏳", "⌛️", "🕐", "🕑", "🕒", "🕓", "🕔", "🕕"]
    for effect in effects:
        print(f"\r🔄 Fetching latest results {effect}", end="", flush=True)
        time.sleep(0.3)

# 🔥 Show Results in a Pro UI
def display_results():
    global last_period, predicted_period, predicted_big_small, history_log
    while True:
        show_banner()
        loading_effect()

        data = fetch_data()
        if data:
            latest_result = data[0]
            current_period, current_number = latest_result.get("issueNumber"), latest_result.get("number")
            current_bs = get_big_small(current_number)

            if predicted_period is None or current_period != predicted_period:
                predicted_period = str(int(current_period) + 1)
                predicted_big_small = predict_next_big_small()

            # ✅ Check Win/Loss
            for result in data:
                period, number = result.get("issueNumber"), result.get("number")                result_bs = get_big_small(number)

                if period == predicted_period:
                    outcome = "✅ Win!" if result_bs == predicted_big_small else "❌ Loss!"
                    history_log.append(f"📅 Period: {period} ({result_bs}) - {outcome}")

                    # 🎯 Set Next Prediction
                    predicted_period = str(int(period) + 1)
                    predicted_big_small = predict_next_big_small()

            # 🎭 Show Animated History + Next Prediction
            os.system('cls' if os.name == 'nt' else 'clear')
            show_banner()
            print("📊 𝗛𝗶𝘀𝘁𝗼𝗿𝘆".center(40))
            print("📝 " + "\n📝 ".join(history_log[-5:]))  # Show last 5 results
            print("\n🎯 𝗡𝗲𝘅𝘁 𝗣𝗿𝗲𝗱𝗶𝗰𝘁𝗶𝗼𝗻".center(40))
            print(f"➡️ Period: {predicted_period} → {predicted_big_small}")

            # ⏳ Refresh Timer
            now = datetime.now(pytz.timezone('Asia/Kolkata'))
            next_refresh = now + timedelta(seconds=(30 - now.second % 30))
            wait_time = (next_refresh - now).seconds
            for i in range(wait_time, 0, -1):
                print(f"\r⏳ Refreshing in {i} sec...", end="", flush=True)
                time.sleep(1)

        else:
            os.system('cls' if os.name == 'nt' else 'clear')
            show_banner()
            print("❌ No data available. Retrying...")

print("🚀 Starting Live Wingo Tracker...")
display_results()
