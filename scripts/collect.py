"""
Daily option chain collector.
Runs via GitHub Actions every trading day at 16:30 ET (after close).
Saves one CSV per symbol per day into data/<SYMBOL>/YYYY-MM-DD.csv
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List

import pandas as pd
import yfinance as yf

# ── Symbols to collect ───────────────────────────────────────────────────────
SYMBOLS = ["AAPL", "GLD", "NVDA", "SPY", "TSLA"]

# How many expiries to collect per symbol
MAX_EXPIRIES = 8

# Output root (relative to repo root)
DATA_DIR = Path(__file__).parent.parent / "data"


def next_expiries(ticker: yf.Ticker, max_count: int) -> List[str]:
    try:
        return list(ticker.options[:max_count])
    except Exception:
        return []


def fetch_chain(ticker: yf.Ticker, expiry: str) -> pd.DataFrame:
    try:
        chain = ticker.option_chain(expiry)
    except Exception as e:
        print(f"    warning: could not fetch {expiry}: {e}")
        return pd.DataFrame()

    calls = chain.calls.copy()
    puts = chain.puts.copy()
    calls["right"] = "C"
    puts["right"] = "P"
    calls["expiry"] = expiry
    puts["expiry"] = expiry
    combined = pd.concat([calls, puts], ignore_index=True)

    rename = {
        "contractSymbol": "contract_symbol",
        "lastTradeDate": "last_trade_date",
        "lastPrice": "last_price",
        "percentChange": "pct_change",
        "openInterest": "open_interest",
        "impliedVolatility": "implied_vol",
        "inTheMoney": "in_the_money",
        "contractSize": "contract_size",
    }
    combined = combined.rename(columns={k: v for k, v in rename.items() if k in combined.columns})

    keep = [
        "expiry", "right", "strike", "bid", "ask", "last_price",
        "volume", "open_interest", "implied_vol", "in_the_money",
        "last_trade_date", "contract_symbol",
    ]
    return combined[[c for c in keep if c in combined.columns]]


def collect_symbol(symbol: str, today: str) -> dict:
    out_dir = DATA_DIR / symbol
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{today}.csv"

    if out_path.exists():
        print(f"  {symbol}: already collected today, skipping")
        return {"symbol": symbol, "date": today, "status": "skipped", "rows": 0}

    print(f"  {symbol}: fetching...")
    ticker = yf.Ticker(symbol)

    try:
        spot = float(ticker.fast_info.last_price)
    except Exception:
        spot = float("nan")

    expiries = next_expiries(ticker, MAX_EXPIRIES)
    if not expiries:
        print(f"  {symbol}: no expiries available")
        return {"symbol": symbol, "date": today, "status": "no_expiries", "rows": 0}

    frames: List[pd.DataFrame] = []
    for expiry in expiries:
        df = fetch_chain(ticker, expiry)
        if not df.empty:
            frames.append(df)

    if not frames:
        return {"symbol": symbol, "date": today, "status": "empty", "rows": 0}

    result = pd.concat(frames, ignore_index=True)
    result.insert(0, "symbol", symbol)
    result.insert(1, "snapshot_date", today)
    result.insert(2, "spot", spot)
    result.to_csv(out_path, index=False)

    rows = len(result)
    print(f"  {symbol}: {rows} rows / {len(frames)} expiries  spot=${spot:.2f}")
    return {"symbol": symbol, "date": today, "status": "ok", "rows": rows,
            "spot": spot, "expiries": len(frames)}


def update_index(summaries: list, today: str) -> None:
    index_path = DATA_DIR / "index.json"
    try:
        existing = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else []
    except Exception:
        existing = []
    existing = [e for e in existing if e.get("date") != today]
    existing.append({"date": today, "symbols": summaries})
    existing.sort(key=lambda e: e["date"])
    index_path.write_text(json.dumps(existing, indent=2, default=str), encoding="utf-8")


def main() -> int:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"\n=== Option Chain Collector  {today} UTC ===\n")
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    summaries = []
    errors = 0
    for symbol in SYMBOLS:
        try:
            summary = collect_symbol(symbol, today)
            summaries.append(summary)
            if summary["status"] not in ("ok", "skipped"):
                errors += 1
        except Exception as exc:
            print(f"  {symbol}: ERROR — {exc}")
            summaries.append({"symbol": symbol, "date": today, "status": "error", "error": str(exc)})
            errors += 1

    update_index(summaries, today)

    print(f"\n{'─'*48}")
    print(f"Done. {len(SYMBOLS) - errors}/{len(SYMBOLS)} symbols OK.")
    for s in summaries:
        icon = "OK" if s["status"] == "ok" else ("--" if s["status"] == "skipped" else "!!")
        print(f"  [{icon}] {s['symbol']:<6}  {s.get('rows', 0):>5} rows")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
