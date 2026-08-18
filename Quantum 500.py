import requests
import time
import os
from colorama import init, Fore
from tenacity import retry, stop_after_attempt, wait_fixed

# Initialize colorama
init()

# API Configuration for Lottery
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json?ts={}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10)",
    "Referer": "https://hgnice.biz"
}

# State Management
state = {
    'history': [],
    'stats': {
        'totalWins': 0,
        'totalLosses': 0,
        'winRate': 0,
        'totalJackpots': 0
    },
    'previous_numbers': [],
    'last_prediction': None  # To store the last prediction for repeat logic
}

# Utility: BIG or SMALL
def get_big_small(number):
    if not isinstance(number, str) or not number.isdigit():
        return "Unknown"
    return "BIG" if int(number) >= 5 else "SMALL"

# Utility: RED or GREEN
def get_color(num):
    if not isinstance(num, str) or not num.isdigit():
        return "Unknown"
    return "RED" if int(num) % 2 == 0 else "GREEN"

# Utility: Check if number is in range
def is_number_in_range(number, range_str):
    if not isinstance(number, str) or not number.isdigit() or range_str == "N/A":
        return False
    try:
        start, end = map(int, range_str.split('-'))
        number = int(number)
        return start <= number <= end
    except:
        return False

# === New Prediction Logic ===
def get_prediction(period: int, last_period: str, last_result: str):
    period_str = str(period)
    last_period_digit = int(last_period[-1]) if last_period and last_period[-1].isdigit() else 0
    last_result_digit = int(last_result) if last_result and last_result.isdigit() else 0
    current_period_digit = int(period_str[-1]) if period_str[-1].isdigit() else 0

    # Step 1: Subtract last period's last digit from last result number
    intermediate = abs(last_result_digit - last_period_digit)
    
    # Step 2: Subtract current period's last digit from the intermediate result
    predicted_number = abs(intermediate - current_period_digit)
    
    # Ensure predicted_number is a single digit (0-9)
    predicted_number = predicted_number % 10
    
    # Determine BIG/SMALL prediction
    prediction = "BIG" if predicted_number >= 5 else "SMALL"
    
    # Set range to N/A since range logic is removed
    predicted_range = "N/A"
    
    return {
        'prediction': prediction,
        'predicted_number': predicted_number,
        'predicted_range': predicted_range,
        'steps': [
            f"Last Period: {last_period}, Last Digit: {last_period_digit}",
            f"Last Result Number: {last_result_digit}",
            f"Intermediate (Last Result - Last Period Digit): {intermediate}",
            f"Current Period: {period_str}, Last Digit: {current_period_digit}",
            f"Predicted Number (Intermediate - Current Period Digit): {predicted_number}",
            f"Prediction: {prediction} (Range: {predicted_range})"
        ]
    }

# Retry Fetch for Lottery API
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def fetch_latest():
    try:
        ts = int(time.time() * 1000)
        response = requests.get(API_URL.format(ts), headers=HEADERS, timeout=5)
        response.raise_for_status()
        data = response.json().get("data", {}).get("list", [])
        if not data:
            raise ValueError("Empty data received")
        return data
    except Exception as e:
        print(f"{Fore.RED}Error fetching data: {e}")
        return []

# Fixed Display History
def display_history(history):
    print(f"\n{Fore.CYAN}📜 Prediction History:")
    print(f"{'Period':<15} {'Predicted':<12} {'Range':<10} {'Actual Size':<12} {'Actual Color':<12} {'Status':<10} {'Jackpot':<10}")
    print("-" * 80)
    for entry in history:
        period = str(entry['period'])
        predicted = entry['predicted']
        predicted_range = str(entry.get('predicted_range', 'N/A'))
        actual_size = str(entry.get('actual_size', 'Pending')) if entry.get('actual_size') is not None else 'Pending'
        actual_color = str(entry.get('actual_color', 'Pending')) if entry.get('actual_color') is not None else 'Pending'
        status = str(entry.get('status', '⏳'))
        jackpot = str(entry.get('jackpot', '⏳'))
        print(f"{period:<15} {predicted:<12} {predicted_range:<10} {actual_size:<12} {actual_color:<12} {status:<10} {jackpot:<10}")

# Main Loop
def run_prediction_tracker():
    seen_periods = set()
    state['history'] = []
    state['previous_numbers'] = []

    try:
        while True:
            data = fetch_latest()
            if not data or not all(key in data[0] for key in ["issueNumber", "number"]):
                print(f"{Fore.RED}No valid data received, using default values...")
                state['previous_numbers'] = []
            else:
                try:
                    state['previous_numbers'] = [item["number"] for item in data[:10] if item.get("number") and item["number"].isdigit()]
                except Exception as e:
                    print(f"{Fore.RED}Error extracting numbers: {e}, using default values...")
                    state['previous_numbers'] = []

            latest = data[0] if data else {"issueNumber": "0", "number": "0"}
            current_period = int(latest["issueNumber"]) if data else 0
            result_number = latest["number"] if data else "0"
            actual_size = get_big_small(result_number)
            actual_color = get_color(result_number)

            if current_period not in seen_periods:
                seen_periods.add(current_period)
                if len(seen_periods) > 100:
                    seen_periods.clear()

                # Update history with actual results
                for entry in state['history']:
                    if entry['period'] == str(current_period) and entry['status'] == '⏳':
                        entry['actual_size'] = actual_size
                        entry['actual_color'] = actual_color
                        entry['status'] = '✅' if entry['predicted'].upper() == actual_size else '❌'
                        if entry['status'] == '✅':
                            state['stats']['totalWins'] += 1
                            state['last_prediction'] = None  # Reset on win
                        else:
                            state['stats']['totalLosses'] += 1
                            # Keep last prediction for repeat
                            state['last_prediction'] = {
                                'prediction': entry['predicted'],
                                'predicted_range': entry['predicted_range']
                            }
                        # Jackpot logic removed since range is now N/A
                        entry['jackpot'] = 'N/A'
                        total = state['stats']['totalWins'] + state['stats']['totalLosses']
                        state['stats']['winRate'] = round((state['stats']['totalWins'] / total) * 100) if total > 0 else 0

                # Predict for next period
                next_period = current_period + 1
                if state['last_prediction'] and state['stats']['totalWins'] + state['stats']['totalLosses'] > 0 and state['history'][-1]['status'] == '❌':
                    # Repeat last prediction if loss
                    prediction = {
                        'prediction': state['last_prediction']['prediction'],
                        'predicted_number': None,
                        'predicted_range': state['last_prediction']['predicted_range'],
                        'steps': [f"Repeating last prediction due to loss: {state['last_prediction']['prediction']} (Range: {state['last_prediction']['predicted_range']})"]
                    }
                else:
                    # New prediction using the calculation
                    last_period = str(current_period)
                    last_result = result_number
                    prediction = get_prediction(next_period, last_period, last_result)

                state['history'].append({
                    'period': str(next_period),
                    'predicted': prediction['prediction'].upper(),
                    'predicted_range': prediction['predicted_range'],
                    'actual_size': None,
                    'actual_color': None,
                    'status': '⏳',
                    'jackpot': 'N/A'
                })
                state['history'] = state['history'][-500:]  # Limit history for efficiency

                # Clear console
                os.system("cls" if os.name == "nt" else "clear")
                print(f"{Fore.LIGHTBLUE_EX}📊 Last 10 Result Numbers: {state['previous_numbers'][:10]}")
                print(f"\n{Fore.GREEN}📈 Current Result:")
                print(f"Period: {current_period}, Number: {result_number}, Size: {actual_size}, Color: {actual_color}")
                # Remove jackpot check since range is N/A
                print(f"\n{Fore.YELLOW}🔮 Prediction (Next Period {next_period}):")
                print(f"Prediction: {prediction['prediction']} (Range: {prediction['predicted_range']})")

                print(f"\n{Fore.MAGENTA}🧮 Formula Steps:")
                for step in prediction['steps']:
                    print(f"  {step}")

                print(f"\n{Fore.BLUE}📊 Statistics:")
                print(f"Wins: {state['stats']['totalWins']}, Losses: {state['stats']['totalLosses']}, Win Rate: {state['stats']['winRate']}%, Jackpots: {state['stats']['totalJackpots']}")
                display_history(state['history'])

            time.sleep(3)

    except KeyboardInterrupt:
        print(f"{Fore.YELLOW}Exited gracefully by user.")

# Start
if __name__ == "__main__":
    run_prediction_tracker()
