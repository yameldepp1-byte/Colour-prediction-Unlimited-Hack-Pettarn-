import requests
import time
import os
import sys

# ✅ API Config
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json?ts={}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10)",
    "Referer": "https://hgnice.biz"
}

# ✅ Check Big/Small from result number
def get_big_small(number):
    try:
        return "BIG" if int(number) >= 5 else "SMALL"
    except Exception as e:
        print(f"Error parsing number {number}: {e}")
        return "Unknown"

# ✅ Custom prediction logic
def predict_next(issue_number):
    try:
        last5 = int(issue_number[-5:])
        predicted_number = (3 * last5 + 1) % 10
        return "BIG" if predicted_number >= 5 else "SMALL"
    except Exception as e:
        print(f"Error predicting for {issue_number}: {e}")
        return "Unknown"

# ✅ Get latest draw data
def fetch_latest():
    try:
        ts = int(time.time() * 1000)
        response = requests.get(API_URL.format(ts), headers=HEADERS, timeout=5)
        response.raise_for_status()
        return response.json().get("data", {}).get("list", [])
    except Exception as e:
        print("⚠️ API fetch error:", e)
        return []

# ✅ Main Logic
def run_prediction_tracker():
    seen_periods = set()
    prediction_history = []  # [{'period': str, 'prediction': str, 'result': ✅❌⏳}]

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

                # ✅ Update previous prediction result if it matches current period
                for item in prediction_history:
                    if item['period'] == current_period and item['result'] == "⏳ waiting...":
                        item['result'] = "✅" if item['prediction'] == actual_result else "❌"
                        break

                # ✅ Predict for next period using custom logic
                next_period = str(int(current_period) + 1)
                next_prediction = predict_next(current_period)

                prediction_history.append({
                    'period': next_period,
                    'prediction': next_prediction,
                    'result': "⏳ waiting..."
                })

                # ✅ Limit to last 10 entries
                prediction_history = prediction_history[-10:]

                # ✅ Clear and display
                os.system('cls' if os.name == 'nt' else 'clear')
                print("🔮 Prediction Tracker (last 10):\n")
                for entry in prediction_history:
                    print(f"{entry['period']} → {entry['prediction']} {entry['result']}")

            # ✅ Adjust wait time (to avoid hammering API)
            time.sleep(10)

    except KeyboardInterrupt:
        print("\n🛑 Stopped by user. Goodbye!")
        sys.exit(0)

# ✅ Start script
if __name__ == "__main__":
    run_prediction_tracker()
