#!/usr/bin/env python3
import os
import sys
import time
import random
import requests

# ✅ ANSI Color Codes for standard console output
COLOR_RED = "\033[91m"
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_BLUE = "\033[94m"
COLOR_CYAN = "\033[96m"
COLOR_MAGENTA = "\033[95m"
COLOR_RESET = "\033[0m"

# ✅ Typewriter effect for smooth animation
def type_writer(text, delay=0.0009):
    """Prints text with a small delay for animation."""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

# ✅ Banner function (Normal Look)
def banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Simple ASCII art banner (or substitute if cfonts is installed)
    title = f"""
{COLOR_RED}===================================={COLOR_RESET}
{COLOR_RED}         POWERFUL BABLU   {COLOR_RESET}
{COLOR_RED}===================================={COLOR_RESET}
"""
    for line in title.split("\n"):
        type_writer(line, delay=0.0001)

    # Simple status line
    print(f"\n{COLOR_YELLOW}>> ACTIVE AI ENGINE | PREDICTION MODE | v1.2 <<{COLOR_RESET}\n")
    print("-" * 40)

# ✅ API Configuration (Kept AS IS - NO CHANGE)
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json?ts={}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10)",
    "Referer": "https://hgnice.biz"
}

# ✅ Helper function to determine BIG or SMALL (Kept AS IS - NO CHANGE)
def get_big_small(number):
    try:
        return "BIG" if int(number) >= 5 else "SMALL"
    except ValueError:
        return "Unknown"

# ✅ Stable Prediction Logic (BN LAST KING Advanced) (Kept AS IS - NO CHANGE)
def stable_prediction(period_number, last_results, prev_prediction=None):
    # --- Prediction Logic Unchanged ---
    recent = last_results[-10:]
    labeled = ["BIG" if int(r) >= 5 else "SMALL" for r in recent]

    big_count = labeled.count("BIG")
    small_count = labeled.count("SMALL")

    if big_count > small_count:
        history_pred = "BIG"
    elif small_count > big_count:
        history_pred = "SMALL"
    else:
        history_pred = "BIG" if int(period_number[-1]) >= 5 else "SMALL"

    try:
        last3_period = int(period_number[-3:])
    except ValueError:
        last3_period = random.randint(100, 999)
    digit_sum = sum(int(d) for d in str(last3_period))
    period_pred = "BIG" if digit_sum % 2 == 0 else "SMALL"

    if history_pred == period_pred:
        base_pred = "SMALL" if history_pred == "BIG" else "BIG"
    else:
        base_pred = history_pred

    if prev_prediction and base_pred == prev_prediction:
        base_pred = "SMALL" if base_pred == "BIG" else "BIG"

    if random.random() < 0.25:
        final_pred = "SMALL" if base_pred == "BIG" else "BIG"
    else:
        final_pred = base_pred

    return final_pred

# ✅ Fetch latest results (Kept AS IS - NO CHANGE)
def fetch_latest():
    try:
        ts = int(time.time() * 1000)
        response = requests.get(API_URL.format(ts), headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json().get("data", {}).get("list", [])
    except requests.RequestException:
        return []

# ✅ Printing and result display (Normal Console Style)
def print_prediction(period, prediction):
    
    # Styles for BIG (Red) and SMALL (Green)
    pred_color = COLOR_RED if prediction == "BIG" else COLOR_GREEN
    
    print(f"\n{COLOR_CYAN}--- NEXT ROUND PREDICTION ---{COLOR_RESET}")
    print(f"  \u23F0 Period:       {COLOR_MAGENTA}{period}{COLOR_RESET}")
    print(f"  \u27A1 Prediction:   {pred_color}{prediction} {COLOR_RESET}") 
    
    sys.stdout.write("  \u2193 Waiting For Result...")
    sys.stdout.flush()

# This function is now simplified and no longer returns a rich status object
def start_waiting_status():
    pass

def print_result(win, period, prediction, actual_number):
    
    # Determine the result message and style
    if win:
        status_text = f"{COLOR_GREEN}\u2714 WIN{COLOR_RESET}" # Check mark
    else:
        status_text = f"{COLOR_RED}\u2716 LOSS{COLOR_RESET}" # X mark
        
    # Overwrite the "Waiting For Result..." line and print the outcome
    sys.stdout.write("\r" + " " * 30 + "\r") # Clear the line
    
    print(f"  \u2193 Result:       {status_text} (Rolled: {COLOR_YELLOW}{actual_number}{COLOR_RESET})")
    print("-" * 40)

# ✅ Main Loop
def run_console():
    banner()
    seen_periods = set()
    last_results = []
    prev_prediction = None
    prediction = None

    while True:
        data = fetch_latest()
        if not data:
            sys.stdout.write(f"\r{COLOR_RED}!! Connection Lost. Retrying... !!{COLOR_RESET}")
            sys.stdout.flush()
            time.sleep(2)
            continue
        
        # Clear the error message if data is successfully fetched
        sys.stdout.write("\r" + " " * 40 + "\r")
        sys.stdout.flush()

        latest = data[0]
        current_period = latest.get("issueNumber", "")
        result_number_str = latest.get("number", "")

        # Store results
        try:
            result_number = int(result_number_str)
            if not last_results or last_results[-1] != result_number:
                last_results.append(result_number)
                if len(last_results) > 20:
                    last_results.pop(0)
        except ValueError:
            result_number = None

        # --- CHECK RESULT ---
        if prediction and prediction["period"] == current_period and result_number is not None:
            
            # The simple UI doesn't need to stop a live spinner, just prints the result
            win = prediction["prediction"] == get_big_small(result_number)
            print_result(win, current_period, prediction["prediction"], result_number)
            prediction = None

        # --- GENERATE NEW PREDICTION ---
        if not prediction and current_period not in seen_periods:
            seen_periods.add(current_period)
            
            # Calculate next period
            next_period_num = int(current_period) + 1 if current_period.isdigit() else 0
            next_period = str(next_period_num)
            
            # Generate the prediction
            next_prediction = stable_prediction(current_period, last_results, prev_prediction)
            prev_prediction = next_prediction

            prediction = {
                "period": next_period,
                "prediction": next_prediction
            }

            show_period = next_period[-5:] if len(next_period) >= 5 else next_period
            
            # Print the Prediction
            print_prediction(show_period, next_prediction)

        time.sleep(3)

# ✅ Run
if __name__ == "__main__":
    try:
        run_console()
    except KeyboardInterrupt:
        print(f"\n\n{COLOR_CYAN}Process terminated by user.{COLOR_RESET}")
        sys.exit(0)

