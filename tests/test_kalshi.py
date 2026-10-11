import json
from pathlib import Path

from marketdata import kalshi

FIX = Path(__file__).parent / "fixtures" / "kxhighny_open.json"


class FakeResp:
    def __init__(self, payload):
        self._p = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._p


class FakeSession:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append(params)
        return FakeResp(self.payload)


def test_fetch_and_rows(tmp_path):
    payload = json.loads(FIX.read_text())
    markets = kalshi.fetch_markets("open", session=FakeSession(payload))
    assert len(markets) == 3
    rows = [kalshi.snapshot_row(m, "2026-10-11T22:00:00+00:00") for m in markets]
    assert rows[0]["mid"] == 0.005
    assert rows[1]["cap_strike"] == 62.0 and rows[1]["floor_strike"] == ""
    # missing ask -> mid stays blank, never extrapolated
    assert rows[2]["yes_ask"] == "" and rows[2]["mid"] == ""

    out = tmp_path / "snap.csv"
    assert kalshi._append(out, kalshi.SNAP_FIELDS, rows) == 3
    assert kalshi._append(out, kalshi.SNAP_FIELDS, rows) == 3  # snapshots always append
    assert len(out.read_text().strip().splitlines()) == 7


def test_results_dedupe(tmp_path):
    m = {"ticker": "X-1", "event_ticker": "X", "result": "yes", "expiration_value": "71"}
    out = tmp_path / "res.csv"
    assert kalshi._append(out, kalshi.RESULT_FIELDS, [kalshi.result_row(m)], key="ticker") == 1
    assert kalshi._append(out, kalshi.RESULT_FIELDS, [kalshi.result_row(m)], key="ticker") == 0
