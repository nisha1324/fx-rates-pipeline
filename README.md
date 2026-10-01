# FX Rates Pipeline: AUD exchange-rate ETL

[![Daily FX refresh](https://github.com/nisha1324/fx-rates-pipeline/actions/workflows/daily.yml/badge.svg)](https://github.com/nisha1324/fx-rates-pipeline/actions/workflows/daily.yml)

> 🚧 **In progress.** The ETL, the SQL report and the daily GitHub Actions schedule all work. Final recommendations come next.

## Why
An Australian business that buys from suppliers in the US, China or Europe, or bills clients in India or Singapore, carries **currency risk**. A 5% move in AUD/USD changes the landed cost of every US invoice by 5%. Finance teams need a reliable, always-current rate history to price quotes, set budget rates and see how much they are exposed.

This project builds that history as a small, production-style **data pipeline**: extract → validate → load. It is designed to run unattended every day.

## Data
- **Source:** [Frankfurter API](https://frankfurter.dev). It is free, needs no API key and serves the **European Central Bank** daily reference rates (business days only).
- **Scope:** base currency **AUD**, quoted against USD, EUR, GBP, CNY, INR, JPY, NZD and SGD, from 2023-01-01 onward.
- **Store:** `data/fx_rates.db`, about 0.5 MB of SQLite. It grows by 8 rows each business day. At the 2026-09-30 snapshot it held 7,656 rows (957 business days × 8 currencies) from 2023-01-02.

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

## Report: what the rates say (snapshot: data to 2026-09-30)
`python -m report.build` runs the four queries in [`sql/`](sql/) against the store and writes [`results/REPORT.md`](results/REPORT.md) plus the charts below. The daily Action regenerates the report and charts, so they move a little each day. The figures quoted in this section are a fixed snapshot as of 2026-09-30.

**1. AUD strength** (`sql/01_aud_strength.sql`). Since 2023-01-02, AUD buys **23.0% more JPY**, 18.5% more INR, 14.8% more NZD and 2.4% more USD. It buys **7.1% less GBP**, 3.7% less EUR and 2.5% less SGD, so UK and European suppliers now cost more in AUD. Japanese and Indian suppliers cost less.

![AUD strength index](results/charts/01_aud_strength_index.png)

**2. Volatility** (`sql/02_volatility.sql`, stdev of daily log returns × √252). AUD/JPY is the most volatile pair (11.5% a year, worst day −5.65%), then AUD/USD (9.7%). AUD/NZD is the calmest (4.7%). A 10% annual swing on a large USD payables book is a real budget risk.

![Volatility](results/charts/02_volatility.png)

**3. Budget-rate variance for a USD importer** (`sql/03_budget_variance.sql`). This assumes USD 100,000 of supplier invoices a month and a budget rate set at the previous December's average AUD/USD (an illustrative policy, not real company data).

| Year | Budget rate | Avg actual | Variance (AUD) |
|---|---|---|---|
| 2024 | 0.6681 | 0.6599 | **−22,806** (over budget) |
| 2025 | 0.6341 | 0.6446 | +30,225 |
| 2026 (Jan–Sep) | 0.6640 | 0.7039 | +76,533 |

The swing between single months ran from −8,032 AUD (Dec 2024) to +11,328 AUD (May 2026). September 2026 runs to the 30th.

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

## Automation (GitHub Actions)
[`.github/workflows/daily.yml`](.github/workflows/daily.yml) runs at **16:30 UTC on weekdays**, after the ECB publishes its rates around 16:00 CET. It can also be started by hand (`workflow_dispatch`). Each run:
1. installs dependencies and runs the offline test suite, so a broken change never touches the data;
2. runs `python -m pipeline.run` (incremental, so on a quiet day it adds 0 rows);
3. rebuilds the report and charts;
4. commits `data/` and `results/` **only if they changed**, as `data: daily FX refresh through <latest date>`.

Runner SQLite builds don't always include the `LN`/`SQRT` math functions that the volatility query needs, so `report/build.py` registers Python fallbacks when they're missing (tested in `tests/test_report_sql.py`). The first manual run on 2026-10-01 loaded 16 new rows (2026-09-29 and 2026-09-30) and committed the refresh itself.

**So what for the business?** Finance gets a rate history and an exposure report that update themselves, with no server to run and no cost, since a public repo gets free Actions minutes. Every refresh is versioned in git, so you can always see which rates a past quote or budget was based on.

## Roadmap
- [x] Extract / transform / validate / load with an audit log and tests
- [x] SQL + chart report: AUD strength by currency, volatility, budget-rate variance for an importer
- [x] GitHub Actions: scheduled daily run that commits new rates and refreshes the report
- [ ] Business findings and recommendations
