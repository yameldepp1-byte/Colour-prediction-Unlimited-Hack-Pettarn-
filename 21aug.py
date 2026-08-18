import requests
import time
import re
from datetime import datetime
from colorama import Fore, init
from collections import Counter

init(autoreset=True)

API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"
BIG_NUMBERS = [1, 2, 3, 4]
SMALL_NUMBERS = [6, 7, 8, 9]
history_data = []
last_fetched_period = None
last_jackpot_number = {}
pending_prediction = None
MAX_HISTORY = 200

def fetch_latest_results():
    try:
        resp = requests.get(API_URL, params={"ts": int(time.time())}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("data", {}).get("list", [])
        if isinstance(results, list):
            return results
        else:
            print(f"{Fore.RED}API response malformed.")
            return []
    except Exception as e:
        print(f"{Fore.RED}Error fetching API: {e}")
        return []

def make_prediction():
    # If little history, alternate simple predictions
    if len(history_data) < 10:
        idx = len(history_data) % 4
        if idx < 2:
            return f"BIG [{BIG_NUMBERS[idx*2]}, {BIG_NUMBERS[idx*2+1]}]"
        else:
            return f"SMALL [{SMALL_NUMBERS[(idx-2)*2]}, {SMALL_NUMBERS[(idx-2)*2+1]}]"
    # Frequency based prediction
    numbers = [item['actual_number'] for item in history_data if item.get('actual_number') is not None]
    freq = Counter(numbers)
    big_sorted = sorted(BIG_NUMBERS, key=lambda x: -freq[x])
    small_sorted = sorted(SMALL_NUMBERS, key=lambda x: -freq[x])
    last_result = history_data[0]['result']
    next_type = "BIG" if last_result == "SMALL" else "SMALL"
    if next_type == "BIG":
        picks = big_sorted[:2] or [1, 3]
        return f"BIG [{picks}, {picks[1]}]"
    else:
        picks = small_sorted[:2] or [7, 9]
        return f"SMALL [{picks}, {picks[1]}]"

def parse_prediction_numbers(prediction):
    m = re.search(r'\[(\d+),\s*(\d+)\]', prediction)
    if m:
        return [int(m.group(1)), int(m.group(2))]
    return []

def update_and_show_stats():
    wins = sum(1 for i in history_data if i.get('status') == 'WIN')
    losses = sum(1 for i in history_data if i.get('status') == 'LOSS')
    jackpots = sum(1 for i in history_data if i.get('jackpot', '').startswith('JACKPOT HIT'))
    accuracy = (wins / (wins + losses) * 100) if wins + losses > 0 else 0
    print(f"\n{Fore.GREEN}Wins: {wins} | {Fore.RED}Losses: {losses} | {Fore.YELLOW}Accuracy: {accuracy:.2f}%")
    print(f"{Fore.GREEN}Jackpot Hits: {jackpots}")
    print("-" * 60)

def show_history():
    print("\nHistory:")
    print("Period           | Prediction      | Result | Jackpot              | Status")
    print("-" * 75)
    for item in history_data[:20]:
        status_icon = f"{Fore.GREEN}✅" if item.get('status') == 'WIN' or item.get('jackpot', '').startswith('JACKPOT HIT') else f"{Fore.RED}❌" if item.get('status') == 'LOSS' else f"{Fore.YELLOW}⏳"
        print(f"{item['period']:<16} | {item['prediction']:<15} | {item['result']:>6} | {item.get('jackpot','Pending'):<20} | {status_icon}")
    print("-" * 75)

def main():
    global history_data, last_fetched_period, pending_prediction

    while True:
        results = fetch_latest_results()
        if not results:
            print(f"{Fore.YELLOW}No data from API, retrying soon...")
            time.sleep(5)
            continue

        latest = results[0]
        period = str(latest["issueNumber"])
        number = int(latest["number"])
        size = "BIG" if number >= 5 else "SMALL"

        if period != last_fetched_period:
            # Update pending prediction with actual results
            if pending_prediction and pending_prediction['period'] == period:
                pending_prediction['actual_number'] = number
                pending_prediction['result'] = size
                pending_prediction['status'] = "WIN" if pending_prediction['prediction'].startswith(size) else "LOSS"

                pred_nums = parse_prediction_numbers(pending_prediction['prediction'])
                last_used = last_jackpot_number.get(pending_prediction['prediction'])
                # Alternate jackpot number
                available = [n for n in pred_nums if n != last_used]
                chosen = available[0] if available else pred_nums
                last_jackpot_number[pending_prediction['prediction']] = chosen

                if number == chosen:
                    pending_prediction['jackpot'] = f"JACKPOT HIT! ({number})"
                else:
                    pending_prediction['jackpot'] = f"No Jackpot (Target {chosen})"

                history_data.insert(0, pending_prediction)
                if len(history_data) > MAX_HISTORY:
                    history_data.pop()

                pending_prediction = None

            last_fetched_period = period
            next_period = str(int(period) + 1)

            # Generate prediction for next period
            if not pending_prediction:
                pred = make_prediction()
                pending_prediction = {
                    "period": next_period,
                    "prediction": pred,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "actual_number": None,
                    "result": "Pending",
                    "status": "Pending",
                    "jackpot": "Pending"
                }
                print(f"\n{Fore.BLUE}>>> Next Prediction for {next_period}: {pred}")

            update_and_show_stats()
            show_history()

        time.sleep(5)

if __name__ == "__main__":
    main()

