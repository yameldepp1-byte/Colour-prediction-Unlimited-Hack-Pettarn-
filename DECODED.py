#!/usr/bin/env python3
import os
import sys
import time
import random
import requests
import webbrowser
from datetime import datetime

# ============================================================
# ⚙️  AETHER PREDICTION SYSTEM v3 – NEON GOD EDITION
# ============================================================

# --- Global Colors (ANSI) ---
RESET  = "\033[0m"
CYAN   = "\033[96m"
MAGENTA= "\033[95m"
PURPLE = "\033[94m"
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BOLD   = "\033[1m"
DIM    = "\033[2m"

# --- Configuration ---
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json?ts={}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10)",
    "Referer": "https://hgnice.biz"
}

# --- Telegram Channel ---
TELEGRAM_CHANNEL = "https://t.me/BNLASTKINGHACK"

# ============================================================
# 🧩 Banner
# ============================================================
def banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    name_tag = f"{BOLD}{MAGENTA}BN LAST KING {RESET}"
    title = f"{BOLD}{CYAN}⛩️ @BN_OWNER @BN_GOD⚡{RESET}"

    print("\n" + CYAN + "═" * 55 + RESET)
    print(title.center(70))
    print(name_tag.center(70))
    print(CYAN + "═" * 55 + RESET + "\n")
    print(f"{PURPLE}Running in NEON MODE... decoding divine predictions...{RESET}\n")

# ============================================================
# 🔗 Auto Join Telegram Channel
# ============================================================
def join_telegram_channel():
    print(f"{YELLOW}🌐 Connecting to Telegram channel...{RESET}")
    try:
        webbrowser.open(TELEGRAM_CHANNEL)
        print(f"{GREEN}✅ Joined Telegram Channel:{RESET} {TELEGRAM_CHANNEL}\n")
    except Exception as e:
        print(f"{RED}⚠️ Unable to open Telegram link:{RESET} {e}\n")
# ============================================================
# 🔮 Determine BIG or SMALL
# ============================================================
def get_big_small(number):
    try:
        return "BIG" if int(number) >= 5 else "SMALL"
    except ValueError:
        return "Unknown"

# ============================================================
# 🧠 Stable Prediction Logic
# ============================================================
def stable_prediction(period_number, last_results, prev_prediction=None):
    recent = last_results[-10:]
    labeled = ["BIG" if r >= 5 else "SMALL" for r in recent]

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

    final_pred = "SMALL" if (random.random() < 0.25 and base_pred == "BIG") else (
        "BIG" if (random.random() < 0.25 and base_pred == "SMALL") else base_pred
    )

    return final_pred

# ============================================================
# 🌐 Fetch Latest API Data
# ============================================================
def fetch_latest():
    try:
        ts = int(time.time() * 1000)
        response = requests.get(API_URL.format(ts), headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json().get("data", {}).get("list", [])
    except requests.RequestException as e:
        print(f"{RED}⚠️  Network Error:{RESET} {e}")
        return []

# ============================================================
# 🎯 Print Prediction Section
# ============================================================
def print_prediction(period, prediction):
    color = RED if prediction == "BIG" else GREEN
    print(PURPLE + "─" * 55 + RESET)
    print(f"{YELLOW}⏳ PERIOD   :{RESET} {BOLD}{period[-7:]}{RESET}")
    print(f"{CYAN}🎯 PREDICT  :{RESET} {color}{BOLD}{prediction}{RESET}")
    sys.stdout.write(f"{MAGENTA}📈 RESULT   : {RESET}")
    sys.stdout.flush()

# ============================================================
# 🧮 Print Win / Loss
# ============================================================
def print_result(win):
    hit = f"{GREEN}💫 HIT{RESET}"
    miss = f"{RED}🌀 MISS{RESET}"
    print(hit if win else miss)
    print(PURPLE + "═" * 55 + RESET + "\n")
    sys.stdout.flush()

# ============================================================
# 🔁 Main Console Loop
# ============================================================
def run_console():
    banner()
    join_telegram_channel()
    seen_periods = set()
    last_results = []
    prev_prediction = None
    prediction = None
    total_predictions = 0
    total_hits = 0

    while True:
        data = fetch_latest()
        if not data:
            time.sleep(3)
            continue

        latest = data[0]
        current_period = str(latest.get("issueNumber", ""))
        result_number = str(latest.get("number", ""))

        try:
            result_int = int(result_number)
            if current_period not in seen_periods:
                last_results.append(result_int)
                if len(last_results) > 20:
                    last_results.pop(0)
        except ValueError:
            pass

        if prediction and prediction["period"] == current_period:
            predicted_result = prediction["prediction"]
            actual_result = get_big_small(result_number)
            win = predicted_result == actual_result

            print_result(win)

            total_predictions += 1
            if win:
                total_hits += 1

            accuracy = (total_hits / total_predictions) * 100 if total_predictions else 0
            print(f"{YELLOW}📊 Accuracy:{RESET} {GREEN}{accuracy:.1f}%{RESET}")
            print(f"{CYAN}🕒 Time:{RESET} {datetime.now().strftime('%H:%M:%S')}")
            print(PURPLE + "═" * 55 + RESET + "\n")

            prev_prediction = predicted_result
            prediction = None
            seen_periods.add(current_period)

        if not prediction and current_period.isdigit():
            try:
                next_period = str(int(current_period) + 1)
            except ValueError:
                time.sleep(3)
                continue

            if next_period in seen_periods:
                time.sleep(1)
                continue

            next_prediction = stable_prediction(current_period, last_results, prev_prediction)
            prediction = {"period": next_period, "prediction": next_prediction}
            print_prediction(next_period, next_prediction)

        time.sleep(1)

# ============================================================
# 🚀 Run
# ============================================================
if __name__ == "__main__":
    run_console()
