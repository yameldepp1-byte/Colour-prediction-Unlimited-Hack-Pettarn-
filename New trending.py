import requests
import time
import os
import sys
from collections import deque, Counter

API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json?ts={}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10)",
    "Referer": "https://hgnice.biz"
}

# ✅ Get BIG/SMALL from number (last digit considered)
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

# ✅ Predict next result using pattern & trend analysis
def predict_next(history_deque):
    if not history_deque:
        return "BIG"  # default if no history yet

    # Frequency-based weight
    counter = Counter(history_deque)
    big_count = counter.get("BIG", 0)
    small_count = counter.get("SMALL", 0)

    # Streak detection: last 3 results
    streak = list(history_deque)[-3:]
    if len(set(streak)) == 1:  # all same
        next_pred = "SMALL" if streak[0] == "BIG" else "BIG"
    else:
        # Weighted by frequency
        next_pred = "BIG" if big_count >= small_count else "SMALL"

    return next_pred

# ✅ Main loop
def run_prediction_tracker():
    seen_periods = set()
    prediction_history = deque(maxlen=100)
    trend_history = deque(maxlen=50)  # last 50 draws

    try:
        while True:
            data = fetch_latest()
            if not data:
                time.sleep(5)
                continue

            latest = data[0]
            current_period = latest['issueNumber']
            result_number = latest['number']
            actual_result = get_big_small(result_number)

            if current_period not in seen_periods:
                seen_periods.add(current_period)
                trend_history.append(actual_result)

                # Update previous prediction result
                for item in prediction_history:
                    if item['period'] == current_period and item['result'] == "⏳ waiting...":
                        item['result'] = "✅" if item['prediction'] == actual_result else "❌"
                        break

                # Predict next period
                next_period = str(int(current_period) + 1)
                next_prediction = predict_next(trend_history)

                prediction_history.append({
                    'period': next_period,
                    'prediction': next_prediction,
                    'result': "⏳ waiting..."
                })

                # Clear & display
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

            time.sleep(5)  # adjust for API timing

    except KeyboardInterrupt:
        print("\n🛑 Stopped by user. Goodbye!")
        sys.exit(0)

if __name__ == "__main__":
    run_prediction_tracker()
