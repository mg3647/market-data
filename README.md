# market-data

Daily market snapshots that can't be recovered later, so they start logging now.

## Kalshi NYC daily high (KXHIGHNY)

Logs every open Central Park daily-high market three times a day, and how past events settled.
It feeds the NYC weather model comparison: your model's probability vs. the market's.

- `data/kalshi/kxhighny_snapshots.csv`: one row per market per snapshot (bid, ask, mid, last, volume, open interest).
- `data/kalshi/kxhighny_results.csv`: one row per settled market (`result` yes/no, `expiration_value` = the official high).
- Missing quotes stay blank. Nothing is interpolated.

Run it by hand (2 minutes):

```
pip install -r requirements.txt
python -m marketdata.kalshi --settled
```

The GitHub Action `kalshi-snapshot.yml` runs it at about 10am, 2pm and 6pm New York time and commits the CSVs.
Public market-data endpoints only: no API key, no trading.

To compare with your model, have the forecast pipeline write `data/model/central_park_probs.csv`
with `event_ticker, ticker, model_prob, made_at_utc`, then join on `ticker`.

## Implied vol logger

The IV snapshot (30-day IV at 90/100/110% moneyness, percentile report for the covered-call trigger)
was built in a separate chat and goes in `marketdata/` alongside this.

## Tests

```
pip install pytest
python -m pytest -q
```
