import requests
import time
import os
import hashlib
import math
from collections import Counter, deque
from colorama import init, Fore
from tenacity import retry, stop_after_attempt, wait_fixed

# ============================
# Setup
# ============================
init(autoreset=True)

API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json?ts={}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10)",
    "Referer": "https://hgnice.biz",
}

CONFIG = {
    "RUN_MODE": None,            # "manual" / "auto" / "backtest"
    "PREDICT_MODE": "ENGINE",    # EXCEL,TREND,REVERSAL,HYBRID,AIPROB,STREAK,ALT,QUANTUM,HYPER,SMART,MATHS,AIcalc,HitRate,TrendTracker,BEST,VOTE,ADAPT,ENGINE
    "FETCH_INTERVAL": 3,
    "HISTORY_LIMIT": 100,
    "BACKTEST_ROUNDS": 80,
}

state = {
    "history": [],
    "stats": {},
    "recent_nums": deque(maxlen=50),   # most-recent-first ints
    "seen_periods": set(),
}

# ============================
# Helpers
# ============================
def safe_str(v): return str(v) if v is not None else "--"

def get_big_small(n):
    if isinstance(n, str):
        if not n.isdigit(): return "Unknown"
        n = int(n)
    if not isinstance(n, int): return "Unknown"
    return "BIG" if n >= 5 else "SMALL"

def clr():
    try: os.system("cls" if os.name == "nt" else "clear")
    except: pass

def winrate(w, l):
    t = w + l
    return round((w / t) * 100, 2) if t > 0 else 0.0

def ema(series, alpha=0.5):
    if not series: return 0.0
    e = series[0]
    for x in series[1:]:
        e = alpha * x + (1 - alpha) * e
    return e

def variance(series):
    if not series: return 0.0
    m = sum(series) / len(series)
    return sum((x - m) ** 2 for x in series) / len(series)

def digits_for_side(side):
    return [5,6,7,8,9] if side == "BIG" else [0,1,2,3,4]

# ============================
# API
# ============================
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def fetch_latest():
    ts = int(time.time() * 1000)
    r = requests.get(API_URL.format(ts), headers=HEADERS, timeout=8)
    r.raise_for_status()
    data = r.json().get("data", {}).get("list", [])
    if not data: raise ValueError("Empty data")
    return data

def extract_recent_numbers(raw_list, limit=50):
    nums = []
    for item in raw_list:
        s = item.get("number")
        if isinstance(s, str) and s.isdigit():
            nums.append(int(s))
    return nums[:limit]

# ============================
# Base Logics (return {'numbers': [..], 'big_small': 'BIG/SMALL/Unknown'})
# ============================
def logic_excel(period, nums):
    if len(nums) < 10: return {"numbers": [], "big_small": "Unknown"}
    last10 = list(nums)[:10]
    diffs = [1 if last10[i] != last10[i+1] else 0 for i in range(9)]
    weighted = [diff * 3 * last10[i] for i, diff in enumerate(diffs)]
    s = sum(weighted)
    result = (s + (period % 1000)) % 10
    return {"numbers": [result], "big_small": "BIG" if result >= 5 else "SMALL"}

def logic_trend(period, nums):
    if not nums: return {"numbers": [], "big_small": "Unknown"}
    K = min(10, len(nums))
    window = list(nums)[:K]
    bs = [get_big_small(n) for n in window]
    bs_pred = "BIG" if bs.count("BIG") >= bs.count("SMALL") else "SMALL"
    top_digit = Counter(window).most_common(1)[0][0]
    return {"numbers": [top_digit], "big_small": bs_pred}

def logic_reversal(period, nums):
    if not nums: return {"numbers": [], "big_small": "Unknown"}
    last = nums[0]
    d = (9 - last) % 10
    return {"numbers": [d], "big_small": "BIG" if d >= 5 else "SMALL"}

def logic_hybrid(period, nums):
    ex = logic_excel(period, nums); tr = logic_trend(period, nums)
    bs = ex["big_small"] if ex["big_small"] == tr["big_small"] else ex["big_small"]
    digits = list(dict.fromkeys(ex["numbers"] + tr["numbers"]))
    return {"numbers": digits[:2], "big_small": bs}

def logic_ai_prob(period, nums):
    if not nums: return {"numbers": [], "big_small": "Unknown"}
    scores = Counter()
    big_score = 0.0; total = 0.0
    for i, n in enumerate(nums):
        w = 1.0 / (i + 1)
        scores[n] += w
        big_score += w if n >= 5 else 0.0
        total += w
    bs = "BIG" if big_score >= (total - big_score) else "SMALL"
    top = [d for d, _ in scores.most_common(2)]
    return {"numbers": top, "big_small": bs}

def logic_streak(period, nums):
    if len(nums) < 3: return {"numbers": [], "big_small": "Unknown"}
    labels = [get_big_small(n) for n in nums[:10]]
    stk_lbl = labels[0]; stk = 1
    for i in range(1, len(labels)):
        if labels[i] == stk_lbl: stk += 1
        else: break
    bs = ("SMALL" if stk_lbl == "BIG" else "BIG") if stk >= 3 else stk_lbl
    med = sorted(nums[:10])[len(nums[:10])//2]
    if bs == "BIG" and med < 5: med = 7
    if bs == "SMALL" and med >= 5: med = 2
    return {"numbers": [med], "big_small": bs}

def logic_alternation(period, nums):
    if len(nums) < 4: return logic_trend(period, nums)
    last4 = [get_big_small(n) for n in nums[:4]]
    alt = all(last4[i] != last4[i-1] for i in range(1,4))
    if alt:
        next_bs = "SMALL" if last4[0] == "BIG" else "BIG"
        d = 6 if next_bs == "BIG" else 3
        return {"numbers": [d], "big_small": next_bs}
    return logic_trend(period, nums)

# === New: QUANTUM (hash-based deterministic) ===
def logic_quantum(period, nums):
    s = f"{period}:{','.join(map(str, nums[:20]))}"
    h = hashlib.md5(s.encode()).hexdigest()
    val = int(h[:6], 16)  # 24-bit
    d = val % 10
    return {"numbers": [d], "big_small": "BIG" if d >= 5 else "SMALL"}

# === New: MATHS (mod/arithmetic features) ===
def logic_maths(period, nums):
    if len(nums) < 6: return {"numbers": [], "big_small": "Unknown"}
    w = nums[:10]
    s = sum(w)
    dif = sum(abs(w[i]-w[i+1]) for i in range(len(w)-1))
    par = sum(n % 2 for n in w)
    d = (s + dif + par + (period % 97)) % 10
    bs = "BIG" if ( (s % 2 == 0 and d >= 4) or d >= 6 ) else ("SMALL" if d <= 3 else ("BIG" if d>=5 else "SMALL"))
    return {"numbers": [d], "big_small": bs}

# === New: AIcalc (hand-crafted linear model + sigmoid) ===
def logic_aicalc(period, nums):
    if len(nums) < 5: return {"numbers": [], "big_small": "Unknown"}
    N = min(12, len(nums))
    w = nums[:N]
    big_ratio = sum(1 for n in w if n>=5) / N
    last = w[0]
    stk = 1
    for i in range(1, N):
        if get_big_small(w[i]) == get_big_small(w[i-1]): stk += 1
        else: break
    series_big = [1 if n>=5 else 0 for n in w]
    e = ema(series_big, 0.45)
    var = variance(w)
    # linear combo (tuned heuristics)
    z = 1.2*big_ratio + 0.6*e + 0.15*stk - 0.08*var + 0.1*((period%10)/9.0) - 0.3
    p = 1/(1+math.exp(-z))
    bs = "BIG" if p>=0.5 else "SMALL"
    d = max(digits_for_side(bs), key=lambda x: -abs(x - (sum(w)/len(w))))
    return {"numbers": [d], "big_small": bs}

# === New: HitRate (recent window hit percentages) ===
def logic_hitrate(period, nums):
    if len(nums) < 8: return {"numbers": [], "big_small": "Unknown"}
    K = min(20, len(nums))
    w = nums[:K]
    big_hits = sum(1 for n in w if n>=5)
    small_hits = K - big_hits
    bs = "BIG" if big_hits >= small_hits else "SMALL"
    modal = Counter([n for n in w if (n>=5) == (bs=='BIG')]).most_common(1)
    d = modal[0][0] if modal else (7 if bs=="BIG" else 2)
    return {"numbers": [d], "big_small": bs}

# === New: TrendTracker (EMA + slope) ===
def logic_trendtracker(period, nums):
    if len(nums) < 5: return {"numbers": [], "big_small": "Unknown"}
    # map to 0/1 for SMALL/BIG
    y = [1 if n>=5 else 0 for n in nums[:20]]
    e = ema(y, 0.5)
    # simple slope: average of diffs
    diffs = [y[i]-y[i+1] for i in range(len(y)-1)]
    slope = sum(diffs) / len(diffs)
    score = 0.7*e + 0.3*((slope+1)/2)
    bs = "BIG" if score>=0.5 else "SMALL"
    # pick digit near side centroid
    side_digits = [n for n in nums[:10] if (n>=5) == (bs=='BIG')]
    centroid = round(sum(side_digits)/len(side_digits)) if side_digits else (7 if bs=="BIG" else 2)
    centroid = int(min(9, max(0, centroid)))
    if bs=="BIG" and centroid<5: centroid=6
    if bs=="SMALL" and centroid>=5: centroid=3
    return {"numbers": [centroid], "big_small": bs}

# ============================
# Ensembles & Meta
# ============================
BASE = {
    "EXCEL": logic_excel, "TREND": logic_trend, "REVERSAL": logic_reversal,
    "HYBRID": logic_hybrid, "AIPROB": logic_ai_prob, "STREAK": logic_streak,
    "ALT": logic_alternation, "QUANTUM": logic_quantum, "MATHS": logic_maths,
    "AIcalc": logic_aicalc, "HitRate": logic_hitrate, "TrendTracker": logic_trendtracker,
}

def ensure_stats_keys():
    for m in list(BASE.keys()) + ["BEST","VOTE","ADAPT","HYPER","SMART","ENGINE"]:
        if m not in state["stats"]:
            state["stats"][m] = {"wins": 0, "losses": 0}

def best_method():
    best = "EXCEL"; best_rate = -1.0
    for m in BASE.keys():
        s = state["stats"].get(m, {"wins":0,"losses":0})
        r = winrate(s["wins"], s["losses"])
        if r > best_rate:
            best_rate, best = r, m
    return best

def vote_mode(period, nums):
    votes_bs = Counter(); votes_digit = Counter()
    for m, f in BASE.items():
        o = f(period, nums)
        if o["big_small"] in ("BIG","SMALL"):
            votes_bs[o["big_small"]] += 1
        for d in o["numbers"]:
            votes_digit[d] += 1
    bs = votes_bs.most_common(1)[0][0] if votes_bs else "Unknown"
    digits = [d for d,_ in votes_digit.most_common(2)]
    return {"numbers": digits, "big_small": bs}

def adapt_mode(period, nums):
    scores_digit = Counter(); scores_bs = Counter()
    for m, f in BASE.items():
        o = f(period, nums)
        s = state["stats"].get(m, {"wins":0,"losses":0})
        w = max(winrate(s["wins"], s["losses"]), 1.0)  # at least 1
        if o["big_small"] in ("BIG","SMALL"):
            scores_bs[o["big_small"]] += w
        for d in o["numbers"]:
            scores_digit[d] += w
    bs = scores_bs.most_common(1)[0][0] if scores_bs else "Unknown"
    digits = [d for d,_ in scores_digit.most_common(2)]
    return {"numbers": digits, "big_small": bs}

# NEW: HYPER (weighted subset ensemble)
def logic_hyper(period, nums):
    weights = {
        "EXCEL": 1.0, "TREND": 0.9, "AIPROB": 1.1, "STREAK": 0.8, "ALT": 0.7,
        "MATHS": 1.0, "TrendTracker": 1.2, "AIcalc": 1.1
    }
    bs_scores = Counter(); d_scores = Counter()
    for m, w in weights.items():
        o = BASE[m](period, nums)
        if o["big_small"] in ("BIG","SMALL"):
            bs_scores[o["big_small"]] += w
        for d in o["numbers"]:
            d_scores[d] += w
    bs = bs_scores.most_common(1)[0][0] if bs_scores else "Unknown"
    digits = [d for d,_ in d_scores.most_common(2)]
    return {"numbers": digits, "big_small": bs}

# NEW: SMART (context-aware: streak+EMA+alt)
def logic_smart(period, nums):
    # Use long streak reversal priority, else EMA momentum, else alternation
    st = logic_streak(period, nums)
    # detect streak length
    if len(nums) >= 4:
        labels = [get_big_small(n) for n in nums[:10]]
        stk_lbl = labels[0]; stk = 1
        for i in range(1, len(labels)):
            if labels[i] == stk_lbl: stk += 1
            else: break
        if stk >= 4:
            return st
    tt = logic_trendtracker(period, nums)
    if tt["big_small"] != "Unknown":
        return tt
    return logic_alternation(period, nums)

# NEW: ENGINE (meta switcher by confidence)
def confidence(outputs):
    if not outputs: return 0.0
    bs_votes = Counter(o["big_small"] for o in outputs if o["big_small"] in ("BIG","SMALL"))
    if not bs_votes: return 0.0
    top = bs_votes.most_common(1)[0][1]
    return round(100 * top / len(outputs), 2)

def logic_engine(period, nums):
    # compute three ensembles
    v = vote_mode(period, nums)
    a = adapt_mode(period, nums)
    h = logic_hyper(period, nums)
    outs = [v, a, h]
    conf = confidence(outs)
    # choose ensemble based on rough confidence level
    chosen = h if conf >= 60 else (a if conf >= 45 else v)
    chosen["__conf"] = conf
    return chosen

# ============================
# Confidence from outputs
# ============================
def confidence_from_map(pred_map):
    return confidence(list(pred_map.values()))

# ============================
# Stats & History
# ============================
def record_result(period, method, predicted_bs, actual_bs, numbers=None, conf=None):
    status = "⏳"
    if actual_bs in ("BIG","SMALL") and predicted_bs in ("BIG","SMALL"):
        status = "✅" if predicted_bs == actual_bs else "❌"
        if method in state["stats"]:
            if status == "✅": state["stats"][method]["wins"] += 1
            else: state["stats"][method]["losses"] += 1
    state["history"].append({
        "period": str(period),
        "method": method,
        "predicted": predicted_bs,
        "numbers": numbers or [],
        "actual": actual_bs if actual_bs else None,
        "status": status,
        "conf": conf,
    })
    state["history"] = state["history"][-CONFIG["HISTORY_LIMIT"]:]

def update_past_to_actual(period, actual_bs):
    for h in state["history"]:
        if h["period"] == str(period) and h["status"] == "⏳":
            h["actual"] = actual_bs
            if h["predicted"] in ("BIG","SMALL"):
                h["status"] = "✅" if h["predicted"] == actual_bs else "❌"
                m = h["method"]
                if m in state["stats"]:
                    if h["status"] == "✅": state["stats"][m]["wins"] += 1
                    else: state["stats"][m]["losses"] += 1

# ============================
# Display
# ============================
def show_header(period, result_digit):
    bs = get_big_small(result_digit)
    print(Fore.GREEN + f"📈 Current: Period={period}, Num={result_digit}, Size={bs}")

def show_predictions(next_period, pred_map, conf=None):
    print(Fore.YELLOW + f"\n🔮 Predictions → Period {next_period}:")
    for m, p in pred_map.items():
        digits = ",".join(map(str, p.get("numbers", []))) if p.get("numbers") else "-"
        print(f"{m:<12} Numbers=[{digits}]  Big/Small={p.get('big_small','Unknown')}")
    if conf is not None:
        print(Fore.CYAN + f"\nConfidence ≈ {conf}%")

def show_history():
    print(Fore.CYAN + f"\n📜 Prediction History (Last {len(state['history'])}):")
    print(f"{'Period':<18} {'Method':<12} {'Pred':<7} {'Nums':<12} {'Actual':<8} {'Conf%':<6} {'Status':<3}")
    print("-"*85)
    for h in state["history"]:
        nums = ",".join(map(str, h.get("numbers") or [])) or "-"
        actual = h["actual"] if h["actual"] else "Pending"
        conf = safe_str(h.get("conf"))
        print(f"{safe_str(h['period']):<18} {safe_str(h['method']):<12} {safe_str(h['predicted']):<7} "
              f"{nums:<12} {actual:<8} {conf:<6} {safe_str(h['status']):<3}")

def show_stats():
    print(Fore.MAGENTA + "\n📊 Stats:")
    ensure_stats_keys()
    for m, s in state["stats"].items():
        print(f"{m:<12} {s['wins']}W/{s['losses']}L → {winrate(s['wins'], s['losses'])}%")

# ============================
# Prediction Engine
# ============================
def predict_for_mode(period, nums):
    ensure_stats_keys()
    mode = CONFIG["PREDICT_MODE"].upper()

    # Build map for display (selected + references)
    pred_map = {}

    # Base methods
    if mode in BASE:
        out = BASE[mode](period, nums)
        pred_map[mode] = out
        conf = confidence_from_map(pred_map)
        return pred_map, out["big_small"], conf

    # Special modes
    if mode == "BEST":
        m = best_method()
        out = BASE[m](period, nums)
        pred_map[m] = out
        return pred_map, out["big_small"], confidence_from_map(pred_map)

    if mode == "VOTE":
        for m, f in BASE.items():
            pred_map[m] = f(period, nums)
        vote = vote_mode(period, nums)
        pred_map["VOTE"] = vote
        return pred_map, vote["big_small"], confidence_from_map(pred_map)

    if mode == "ADAPT":
        for m, f in BASE.items():
            pred_map[m] = f(period, nums)
        adapt = adapt_mode(period, nums)
        pred_map["ADAPT"] = adapt
        return pred_map, adapt["big_small"], confidence_from_map(pred_map)

    if mode == "HYPER":
        for m, f in BASE.items():
            pred_map[m] = f(period, nums)
        hyp = logic_hyper(period, nums)
        pred_map["HYPER"] = hyp
        return pred_map, hyp["big_small"], confidence_from_map(pred_map)

    if mode == "SMART":
        # show key references + smart
        for m in ["STREAK","TrendTracker","ALT"]:
            pred_map[m] = BASE[m](period, nums)
        sm = logic_smart(period, nums)
        pred_map["SMART"] = sm
        return pred_map, sm["big_small"], confidence_from_map(pred_map)

    if mode == "ENGINE":
        for m in ["EXCEL","TREND","AIPROB","STREAK","ALT","MATHS","TrendTracker","AIcalc","QUANTUM"]:
            pred_map[m] = BASE[m](period, nums)
        eng = logic_engine(period, nums)
        pred_map["ENGINE"] = {k:v for k,v in eng.items() if not k.startswith("__")}
        conf = eng.get("__conf", confidence_from_map(pred_map))
        return pred_map, eng["big_small"], conf

    # Fallback
    out = BASE["EXCEL"](period, nums)
    pred_map["EXCEL"] = out
    return pred_map, out["big_small"], confidence_from_map(pred_map)

# ============================
# Backtesting
# ============================
def backtest(raw_data, rounds=60):
    ensure_stats_keys()
    seq = []
    for item in raw_data[:rounds+10]:
        s = item.get("number"); per = item.get("issueNumber")
        if isinstance(s, str) and s.isdigit():
            seq.append((int(per), int(s)))
    if len(seq) < 12:
        print(Fore.RED + "Not enough data for backtest."); return

    wins = losses = 0
    per_stats = {k: {"w":0,"l":0} for k in list(BASE.keys())+["BEST","VOTE","ADAPT","HYPER","SMART","ENGINE"]}

    for i in range(len(seq)-1):
        cur_period, cur_digit = seq[i]        # known result at step i
        next_period = seq[i-1][0] if i>0 else cur_period+1
        window = [d for _, d in seq[i:i+50]]

        pred_map, pred_bs, _ = predict_for_mode(next_period, window)
        actual_bs = get_big_small(seq[i-1][1] if i>0 else cur_digit)

        if pred_bs in ("BIG","SMALL"):
            if pred_bs == actual_bs: wins += 1
            else: losses += 1

        # base methods
        for m, f in BASE.items():
            o = f(next_period, window)
            if o["big_small"] in ("BIG","SMALL"):
                if o["big_small"] == actual_bs: per_stats[m]["w"] += 1
                else: per_stats[m]["l"] += 1
        # ensembles
        for name, func in [("BEST", None), ("VOTE", vote_mode), ("ADAPT", adapt_mode),
                           ("HYPER", logic_hyper), ("SMART", logic_smart), ("ENGINE", logic_engine)]:
            if name == "BEST":
                bm = best_method(); o = BASE[bm](next_period, window)
            else:
                o = func(next_period, window)
            bs = o["big_small"]
            if bs in ("BIG","SMALL"):
                if bs == actual_bs: per_stats[name]["w"] += 1
                else: per_stats[name]["l"] += 1

    total = wins + losses
    print(Fore.CYAN + f"\n🧪 Backtest (~{rounds} rounds): Mode={CONFIG['PREDICT_MODE']}")
    print(f"Primary Accuracy: {round((wins/total)*100,2) if total>0 else 0}% ({wins}W/{losses}L)")
    print("\nPer-Method Accuracies:")
    for m, s in per_stats.items():
        t = s["w"] + s["l"]
        rate = round((s["w"]/t)*100,2) if t>0 else 0.0
        print(f"{m:<13} {s['w']}W/{s['l']}L → {rate}%")

# ============================
# Modes
# ============================
def manual_mode():
    print(Fore.YELLOW + "\n🖐️ Manual: enter most-recent digits (0-9). Type 'go' to predict, 'q' to quit.")
    local = deque(maxlen=50)
    while True:
        s = input("Enter digit or 'go'/'q': ").strip().lower()
        if s == 'q': break
        if s == 'go':
            if not local: print("Add some digits first."); continue
