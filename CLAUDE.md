# market-data: notes for Claude

Daily snapshots of market data that can't be recovered later. Owner: Matt (not a programmer).
Write to him in plain words, lead with the answer, keep it short.

## Rules
- Public data only. Never put employer (Bloomberg) data or any licensed data in this repo.
- No API keys or tokens in git. No trading code.
- Missing values stay blank. Never interpolate or extrapolate a snapshot.
- Logs only append. Never rewrite past rows; fix bad rows with a dated correction note.
- Before trusting any signal built on this data, run a skeptic pass: sample size, look-ahead, how many variants were tried, comparison with a simple baseline.

## Layout
- `marketdata/kalshi.py`: Kalshi KXHIGHNY (Central Park daily high) snapshot and settled-result logger.
- `data/kalshi/`: snapshot and result CSVs, committed by `.github/workflows/kalshi-snapshot.yml`.
- `tests/`: `python -m pytest -q`.
