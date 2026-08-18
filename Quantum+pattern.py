import requests
import time
import os
import sys
import random
from collections import Counter
import math

# ✅ API Config (30s Game)
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json?ts={}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10)",
    "Referer": "https://hgnice.biz"
}

# ✅ Convert number to BIG/SMALL
def get_big_small(number):
    try:
        return "BIG" if int(number) >= 5 else "SMALL"
    except:
        return "Unknown"

# ✅ Safe Clear Screen
def safe_clear():
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
    except:
        pass

# ✅ Fetch latest draws with retry
def fetch_latest(retries=3, delay=1):
    for i in range(retries):
        try:
            ts = int(time.time() * 1000)
            response = requests.get(API_URL.format(ts), headers=HEADERS, timeout=5)
            response.raise_for_status()
            return response.json().get("data", {}).get("list", [])
        except Exception as e:
            if i < retries - 1:
                time.sleep(delay * (2 ** i))  # exponential backoff
            else:
                print("⚠️ API fetch error:", e)
    return []

# 🪙 Quantum-inspired single-qubit predictor
def quantum_inspired_predictor(history, window=50, shots=1, randomness=0.02):
    """
    Simulate a single qubit whose rotation angle encodes bias in recent results.
    - window: how many past verified results to consider
    - shots: number of measurements to take (1 by default)
    - randomness: small extra noise to emulate quantum noise / uncertainty (0..1)
    Returns: (prediction, {"BIG": p_big_percent, "SMALL": p_small_percent})
    Notes: This is a classical simulation that produces probabilistic outputs.
    """
    # Collect last `window` actual results that are known (BIG/SMALL)
    last_results = [h['actual'] for h in history if h['actual'] in ("BIG", "SMALL")][-window:]
    if not last_results or len(last_results) < 2:
        # Not enough data → initialize nearly unbiased
        p_big = 0.5
        p_small = 0.5
    else:
        counts = Counter(last_results)
        big_count = counts["BIG"]
        small_count = counts["SMALL"]
        # bias in [-1, 1]
        bias = (big_count - small_count) / float(window)
        # map bias to rotation angle theta in [0, pi]
        # bias = -1 -> theta = 0 (|0> mostly) -> SMALL
        # bias =  0 -> theta = pi/2 -> 50/50
        # bias =  1 -> theta = pi (|1> mostly) -> BIG
        theta = (bias + 1) / 2.0 * math.pi
        # probability of measuring |1> (we map that to BIG)
        p_big = math.sin(theta / 2.0) ** 2
        p_small = 1.0 - p_big

        # Inject a tiny quantum-like noise so probabilities never go exactly 0 or 1
        # scale noise by `randomness` parameter
        noise = (random.random() - 0.5) * 2 * randomness  # in [-rand, +rand]
        p_big = min(max(p_big + noise, 0.0001), 0.9999)
        p_small = 1.0 - p_big

    # If multiple shots requested, take majority of shot outcomes
    measured_ones = 0
    for _ in range(shots):
        r = random.random()
        if r < p_big:
            measured_ones += 1

    # Decision rule: if majority of shots measured 1 => BIG else SMALL
    pred = "BIG" if measured_ones >= (shots / 2.0) else "SMALL"

    # Return probabilities as percentages rounded to 2 decimals
    return pred, {"BIG": round(p_big * 100, 2), "SMALL": round(p_small * 100, 2)}

# ✅ Update accuracy using API verified results
def update_accuracy(prediction_history):
    data = fetch_latest()
    if not data:
        return prediction_history

    results_map = {d['issueNumber']: get_big_small(d['number']) for d in data}

    for item in prediction_history:
        if item['actual'] == "⏳":
            if item['period'] in results_map:
                actual = results_map[item['period']]
                item['actual'] = actual
                item['result'] = "✅" if item['prediction'] == actual else "❌"

    return prediction_history

# ✅ Accuracy calculation
def calc_accuracy(history):
    results = [1 if h['result'] == "✅" else 0 for h in history if h['result'] in ["✅", "❌"]]
    return (sum(results) / len(results) * 100) if results else 0.0

# ✅ Main loop (uses quantum_inspired_predictor instead of previous hybrid)
def run_prediction_tracker():
    seen_periods = set()
    prediction_history = []

    try:
        while True:
            prediction_history = update_accuracy(prediction_history)

            data = fetch_latest()
            if not data:
                time.sleep(5)
                continue

            latest = data[0]
            current_period = latest['issueNumber']

            if current_period not in seen_periods:
                seen_periods.add(current_period)

                # Next period prediction (quantum-inspired)
                next_period = str(int(current_period) + 1)
                # You can increase `shots` for lower variance, or `randomness` for more exploration
                next_prediction, probs = quantum_inspired_predictor(prediction_history, window=50, shots=1, randomness=0.03)

                prediction_history.append({
                    'period': next_period,
                    'prediction': next_prediction,
                    'actual': "⏳",
                    'result': "⏳"
                })

                prediction_history = prediction_history[-500:]

                # Display
                safe_clear()
                print("🧪 Quantum-Inspired Pattern Tracker (Last 50 results)\n")
                for entry in prediction_history[-20:]:
                    print(f"{entry['period']} → {entry['prediction']} | {entry['result']}")

                print("\n🔮 Next Prediction:", next_prediction)
                print("📈 BIG:", probs["BIG"], "% | SMALL:", probs["SMALL"], "%")
                print("✅ Accuracy (All): {:.2f}%".format(calc_accuracy(prediction_history)))

            # Sleep a short amount; for a 30s cycle you might want ~1-2 seconds
            time.sleep(2)

    except KeyboardInterrupt:
        print("\n🛑 Stopped by user. Goodbye!")
        sys.exit(0)

# ✅ Start
if __name__ == "__main__":
    run_prediction_tracker()
