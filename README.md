# FX Rates Pipeline: AUD exchange-rate ETL

> 🚧 **In progress.** The ETL core and the SQL report work. The GitHub Actions schedule is next.

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

## Report: what the rates say (data to 2026-09-28)
`python -m report.build` runs the four queries in [`sql/`](sql/) against the store and writes [`results/REPORT.md`](results/REPORT.md) plus the charts below.

**1. AUD strength** (`sql/01_aud_strength.sql`). Since 2023-01-02, AUD buys **23.9% more JPY**, 19.7% more INR, 15.2% more NZD and 3.2% more USD. It buys **6.2% less GBP** and 3.1% less EUR, so UK and European suppliers now cost more in AUD. Japanese and Indian suppliers cost less.

![AUD strength index](results/charts/01_aud_strength_index.png)

**2. Volatility** (`sql/02_volatility.sql`, stdev of daily log returns × √252). AUD/JPY is the most volatile pair (11.5% a year, worst day −5.65%), then AUD/USD (9.7%). AUD/NZD is the calmest (4.7%). A 10% annual swing on a large USD payables book is a real budget risk.

![Volatility](results/charts/02_volatility.png)

**3. Budget-rate variance for a USD importer** (`sql/03_budget_variance.sql`). This assumes USD 100,000 of supplier invoices a month and a budget rate set at the previous December's average AUD/USD (an illustrative policy, not real company data).

| Year | Budget rate | Avg actual | Variance (AUD) |
|---|---|---|---|
| 2024 | 0.6681 | 0.6599 | **−22,806** (over budget) |
| 2025 | 0.6341 | 0.6446 | +30,225 |
| 2026 (Jan–Sep) | 0.6640 | 0.7041 | +76,801 |

The swing between single months ran from −8,032 AUD (Dec 2024) to +11,328 AUD (May 2026). September 2026 is a partial month, up to the 28th.

![Budget variance](results/charts/03_budget_variance_usd.png)

**So what for the business?** Even a simple budget-rate policy is off by tens of thousands of AUD a year on a modest USD spend, and the error changes sign from year to year. That argues for (a) re-forecasting the budget rate quarterly rather than annually, (b) hedging a share of committed USD and JPY payables, where volatility is highest, and (c) reviewing GBP/EUR supplier pricing, since AUD has weakened against both.

## How to run
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m pipeline.run     # backfill on first run, then incremental
python -m report.build     # SQL report -> results/REPORT.md + charts
pytest -q                  # offline tests (no network)
```
Output from a real first run and an immediate rerun:
```
from 2023-01-01: fetched 7640 rows, 7640 new; table now 7640 rows, latest 2026-09-28
from 2026-09-29: fetched 0 rows, 0 new; table now 7640 rows, latest 2026-09-28
```

## Roadmap
- [x] Extract / transform / validate / load with an audit log and tests
- [x] SQL + chart report: AUD strength by currency, volatility, budget-rate variance for an importer
- [ ] GitHub Actions: scheduled daily run that commits new rates and refreshes the report
- [ ] Business findings and recommendations
