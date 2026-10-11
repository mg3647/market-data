"""Kalshi NYC daily-high temperature logger.

Snapshots every open market in the KXHIGHNY series (Central Park daily high)
and appends one row per market to data/kalshi/kxhighny_snapshots.csv.
With --settled it also records how recent events actually resolved, in
data/kalshi/kxhighny_results.csv, so your model can be scored later.

Public market-data endpoints only: no API key, no trading.

Usage:
    python -m marketdata.kalshi             # snapshot open markets
    python -m marketdata.kalshi --settled   # also log settled results
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import sys
from pathlib import Path

import requests

API = "https://api.elections.kalshi.com/trade-api/v2/markets"
SERIES = "KXHIGHNY"
ROOT = Path(__file__).resolve().parent.parent
SNAP_PATH = ROOT / "data" / "kalshi" / "kxhighny_snapshots.csv"
RESULT_PATH = ROOT / "data" / "kalshi" / "kxhighny_results.csv"

SNAP_FIELDS = [
    "snapshot_utc", "event_ticker", "ticker", "strike_type", "floor_strike",
    "cap_strike", "label", "yes_bid", "yes_ask", "mid", "last_price",
    "volume", "open_interest", "close_time",
]
RESULT_FIELDS = [
    "event_ticker", "ticker", "strike_type", "floor_strike", "cap_strike",
    "label", "result", "expiration_value", "close_time",
]


def _num(value):
    """Kalshi sends prices/sizes as strings; blank stays blank (never guessed)."""
    if value is None or value == "":
        return ""
    try:
        return float(value)
    except (TypeError, ValueError):
        return ""


def fetch_markets(status: str, session=None, max_pages: int = 20) -> list[dict]:
    session = session or requests.Session()
    markets, cursor = [], None
    for _ in range(max_pages):
        params = {"series_ticker": SERIES, "status": status, "limit": 200}
        if cursor:
            params["cursor"] = cursor
        resp = session.get(API, params=params, timeout=30)
        resp.raise_for_status()
        payload = resp.json()
        markets.extend(payload.get("markets", []))
        cursor = payload.get("cursor")
        if not cursor:
            break
    return markets


def snapshot_row(m: dict, now_utc: str) -> dict:
    bid, ask = _num(m.get("yes_bid_dollars")), _num(m.get("yes_ask_dollars"))
    mid = round((bid + ask) / 2, 4) if bid != "" and ask != "" else ""
    return {
        "snapshot_utc": now_utc,
        "event_ticker": m.get("event_ticker", ""),
        "ticker": m.get("ticker", ""),
        "strike_type": m.get("strike_type", ""),
        "floor_strike": _num(m.get("floor_strike")),
        "cap_strike": _num(m.get("cap_strike")),
        "label": m.get("yes_sub_title", ""),
        "yes_bid": bid,
        "yes_ask": ask,
        "mid": mid,
        "last_price": _num(m.get("last_price_dollars")),
        "volume": _num(m.get("volume_fp")),
        "open_interest": _num(m.get("open_interest_fp")),
        "close_time": m.get("close_time", ""),
    }


def result_row(m: dict) -> dict:
    return {
        "event_ticker": m.get("event_ticker", ""),
        "ticker": m.get("ticker", ""),
        "strike_type": m.get("strike_type", ""),
        "floor_strike": _num(m.get("floor_strike")),
        "cap_strike": _num(m.get("cap_strike")),
        "label": m.get("yes_sub_title", ""),
        "result": m.get("result", ""),
        "expiration_value": m.get("expiration_value", ""),
        "close_time": m.get("close_time", ""),
    }


def _append(path: Path, fields: list[str], rows: list[dict], key=None) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = set()
    if key and path.exists():
        with path.open(newline="") as f:
            existing = {row[key] for row in csv.DictReader(f)}
    new = [r for r in rows if not key or r[key] not in existing]
    write_header = not path.exists() or path.stat().st_size == 0
    with path.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if write_header:
            w.writeheader()
        w.writerows(new)
    return len(new)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--settled", action="store_true", help="also log settled results")
    args = ap.parse_args(argv)

    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    open_markets = fetch_markets("open")
    n = _append(SNAP_PATH, SNAP_FIELDS, [snapshot_row(m, now) for m in open_markets])
    print(f"{now}: logged {n} open {SERIES} markets")

    if args.settled:
        settled = fetch_markets("settled", max_pages=2)
        k = _append(RESULT_PATH, RESULT_FIELDS, [result_row(m) for m in settled], key="ticker")
        print(f"logged {k} newly settled markets")
    if n == 0:
        print("warning: no open markets returned", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
