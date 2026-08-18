import requests
import time
import os
import sys
from colorama import Fore, Style, init

# ✅ Initialize colorama
init(autoreset=True)

# ✅ API Config
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json?ts={}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10)",
    "Referer": "https://hgnice.biz"
}

# ✅ Big/Small checker
def get_big_small(number: str) -> str:
    try:
        return "BIG" if int(number) >= 5 else "SMALL"
    except:
        return "Unknown"

# ✅ Custom prediction logic
def predict_next(issue_number: str) -> str:
    try:
        last5 = int(issue_number[-5:])
        predicted_number = (3 * last5 + 1) % 10
        return "BIG" if predicted_number >= 5 else "SMALL"
    except:
        return "Unknown"

# ✅ Fetch latest result
def fetch_latest():
    try:
        ts = int(time.time() * 1000)
        response = requests.get(API_URL.format(ts), headers=HEADERS, timeout=5)
        response.raise_for_status()
        return response.json().get("data", {}).get("list", [])
    except Exception as e:
        print(Fore.RED + f"⚠️ API fetch error: {e}")
        return []

# ✅ Main logic
def run_prediction_tracker():
    seen_periods = set()
    prediction_history = []  # [{'period': str, 'prediction': str, 'result': ✅❌⏳}]
    result_history = []      # [{'period': str, 'number': str, 'size': BIG/SMALL}]

    try:
        while True:
            data = fetch_latest()
            if not data:
                time.sleep(5)
                continue

            latest = data[0]
            current_period = latest.get("issueNumber")
            result_number = latest.get("number")

            if not current_period or result_number is None:
                time.sleep(5)
                continue

            actual_result = get_big_small(result_number)

            if current_period not in seen_periods:
                seen_periods.add(current_period)

                # ✅ Store actual result
                result_history.append({
                    'period': current_period,
                    'number': result_number,
                    'size': actual_result
                })
                result_history = result_history[-20:]  # keep last 20

                # ✅ Update previous prediction
                for item in prediction_history:
                    if item['period'] == current_period and item['result'] == "⏳ waiting...":
                        item['result'] = "✅" if item['prediction'] == actual_result else "❌"
                        break

                # ✅ Predict next period
                next_period = str(int(current_period) + 1)
                next_prediction = predict_next(current_period)

                prediction_history.append({
                    'period': next_period,
                    'prediction': next_prediction,
                    'result': "⏳ waiting..."
                })

                prediction_history = prediction_history[-20:]  # keep last 20

                # ✅ Calculate accuracy
                valid_results = [p['result'] for p in prediction_history if p['result'] in ["✅", "❌"]]
                accuracy = (valid_results.count("✅") / len(valid_results) * 100) if valid_results else 0

                # ✅ Clear console
                os.system('cls' if os.name == 'nt' else 'clear')

                # ✅ Show actual results
                print(Fore.MAGENTA + "🎲 Last 20 Actual Results:\n" + Style.RESET_ALL)
                for res in result_history:
                    print(f"{res['period']} → Number: {res['number']} → {res['size']}")

                # ✅ Show predictions
                print(Fore.CYAN + "\n🔮 Last 20 Predictions:\n" + Style.RESET_ALL)
                for entry in prediction_history:
                    color = Fore.GREEN if entry['result'] == "✅" else (Fore.RED if entry['result'] == "❌" else Fore.YELLOW)
                    print(f"{entry['period']} → {entry['prediction']} {color}{entry['result']}{Style.RESET_ALL}")

                print(f"\n📊 Accuracy (last {len(valid_results)}): {accuracy:.2f}%")

            # ✅ Fetch every 6s
            time.sleep(6)

    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n🛑 Stopped by user. Goodbye!")
        sys.exit(0)


# ✅ Start script
if __name__ == "__main__":
    run_prediction_tracker()
