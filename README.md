# FX Rates Pipeline: AUD exchange-rate ETL

> 🚧 **In progress.** The ETL core works. The report and the GitHub Actions schedule are next.

## Why
An Australian business that buys from suppliers in the US, China or Europe, or bills clients in India or Singapore, carries **currency risk**. A 5% move in AUD/USD changes the landed cost of every US invoice by 5%. Finance teams need a reliable, always-current rate history to price quotes, set budget rates and see how much they are exposed.

This project builds that history as a small, production-style **data pipeline**: extract → validate → load. It is designed to run unattended every day.

## Data
- **Source:** [Frankfurter API](https://frankfurter.dev). It is free, needs no API key and serves the **European Central Bank** daily reference rates (business days only).
- **Scope:** base currency **AUD**, quoted against USD, EUR, GBP, CNY, INR, JPY, NZD and SGD, from 2023-01-01 onward.
- **Current store:** 7,640 rows (955 business days × 8 currencies), from 2023-01-02 to 2026-09-28, in `data/fx_rates.db`, about 0.5 MB of SQLite.

## Pipeline design
```
Frankfurter API ──► extract.py ──► transform.py ──► load.py ──► data/fx_rates.db
  (JSON, ECB)       retries +       flatten to        idempotent      fx_rates
                    backoff         tidy rows +       upsert on       pipeline_runs
                                    validation        (date,base,quote)
```
| Concern | How it's handled |
|---|---|
| **Incremental loads** | Each run asks for data only after the latest stored date. On an empty DB it backfills from `START_DATE`. |
| **Idempotency** | The primary key is `(date, base, quote)` with `ON CONFLICT DO UPDATE`, so a rerun adds 0 rows. |
| **Data quality** | Before loading, the run fails loudly on nulls, non-positive rates, duplicate keys or malformed dates. |
| **API quirks** | Frankfurter moves a range start back to the previous business day, so those rows are dropped to keep loads strictly incremental. |
| **Auditability** | Each run writes a row to `pipeline_runs` with the timestamp, requested start, rows fetched, rows new and latest date. |
| **Transient failures** | 3 attempts with exponential backoff. |

## How to run
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m pipeline.run     # backfill on first run, then incremental
pytest -q                  # offline tests (no network)
```
Output from a real first run and an immediate rerun:
```
from 2023-01-01: fetched 7640 rows, 7640 new; table now 7640 rows, latest 2026-09-28
from 2026-09-29: fetched 0 rows, 0 new; table now 7640 rows, latest 2026-09-28
```

## Roadmap
- [x] Extract / transform / validate / load with an audit log and tests
- [ ] SQL + chart report: AUD strength by currency, volatility, budget-rate variance for an importer
- [ ] GitHub Actions: scheduled daily run that commits new rates and refreshes the report
- [ ] Business findings and recommendations
