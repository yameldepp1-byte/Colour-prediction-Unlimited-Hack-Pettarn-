import requests
import time
import os
import sys
import random
from collections import deque, Counter

# ✅ API Config (30s Game)
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json?ts={}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10)",
    "Referer": "https://hgnice.biz"
}

# ✅ Get BIG/SMALL from number
def get_big_small(number):
    try:
        return "BIG" if int(str(number)[-1]) >= 5 else "SMALL"
    except:
        return "Unknown"

# ✅ Fetch latest draw data
def fetch_latest():
    try:
        ts = int(time.time() * 1000)
        response = requests.get(API_URL.format(ts), headers=HEADERS, timeout=5)
        response.raise_for_status()
        return response.json().get("data", {}).get("list", [])
    except Exception as e:
        print("⚠️ API fetch error:", e)
        return []

# ✅ Pattern + Random Hybrid Predictor
def predict_next(history):
    if len(history) < 5:
        return random.choice(["BIG", "SMALL"])  # random if very little history

    # --- Frequency analysis ---
    freq = Counter(history[-50:])  
    big_weight = freq["BIG"]
    small_weight = freq["SMALL"]

    # --- Streak analysis ---
    streak = 1
    last = history[-1]
    for i in range(len(history) - 2, -1, -1):
        if history[i] == last:
            streak += 1
        else:
            break
    if streak >= 3:  # anti-streak bias
        if last == "BIG":
            small_weight += streak
        else:
            big_weight += streak

    # --- Sequence analysis ---
    if len(history) >= 3:
        seq = tuple(history[-3:])
        following = []
        for i in range(len(history) - 3):
            if tuple(history[i:i + 3]) == seq:
                if i + 3 < len(history):
                    following.append(history[i + 3])
        if following:
            seq_freq = Counter(following)
            big_weight += seq_freq["BIG"]
            small_weight += seq_freq["SMALL"]

    # --- Controlled randomness (10–20% chance to flip) ---
    prediction = "BIG" if big_weight >= small_weight else "SMALL"
    if random.random() < 0.15:  # 15% randomness
        prediction = "BIG" if prediction == "SMALL" else "SMALL"

    return prediction

# ✅ Main loop
def run_prediction_tracker():
    seen_periods = set()
    prediction_history = deque(maxlen=100)
    trend_history = deque(maxlen=100)

    try:
        while True:
            data = fetch_latest()
            if not data:
                time.sleep(5)
                continue

            latest = data[0]
            current_period = latest['issueNumber']
            result_number = str(latest.get('number', '0'))
            actual_result = get_big_small(result_number)

            if current_period not in seen_periods:
                seen_periods.add(current_period)
                trend_history.append(actual_result)

                # ✅ Update previous prediction result
                for item in prediction_history:
                    if item['period'] == current_period and item['result'] == "⏳ waiting...":
                        item['result'] = "✅" if item['prediction'] == actual_result else "❌"
                        break

                # ✅ Predict next period
                next_period = str(int(current_period) + 1)
                next_prediction = predict_next(list(trend_history))

                prediction_history.append({
                    'period': next_period,
                    'prediction': next_prediction,
                    'result': "⏳ waiting..."
                })

                # ✅ Display results
                os.system('cls' if os.name == 'nt' else 'clear')
                print("🔮 Prediction Tracker (last 10):\n")
                correct = 0
                total = 0
                for entry in prediction_history:
                    print(f"{entry['period']} → {entry['prediction']} {entry['result']}")
                    if entry['result'] in ["✅","❌"]:
                        total += 1
                        if entry['result'] == "✅":
                            correct += 1
                accuracy = (correct / total * 100) if total > 0 else 0
                print(f"\n📊 Accuracy: {accuracy:.2f}%")

            time.sleep(10)

    except KeyboardInterrupt:
        print("\n🛑 Stopped by user. Goodbye!")
        sys.exit(0)

# ✅ Start
if __name__ == "__main__":
    run_prediction_tracker()
