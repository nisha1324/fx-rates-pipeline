"""Run the ETL: backfill on first run, then fetch only days not yet stored.

    python -m pipeline.run
"""
from datetime import date, timedelta

from pipeline.config import BASE, DB_PATH, START_DATE
from pipeline.extract import fetch_range
from pipeline.load import connect, latest_date, log_run, upsert
from pipeline.transform import to_rows, validate


def main() -> None:
    conn = connect(DB_PATH)
    last = latest_date(conn, BASE)
    start = START_DATE if last is None else (date.fromisoformat(last) + timedelta(days=1)).isoformat()

    df = validate(to_rows(fetch_range(start), start=start))
    with conn:
        new = upsert(conn, df)
        latest = latest_date(conn, BASE)
        log_run(conn, start, len(df), new, latest)
    total = conn.execute("SELECT COUNT(*) FROM fx_rates").fetchone()[0]
    conn.close()
    print(f"from {start}: fetched {len(df)} rows, {new} new; "
          f"table now {total} rows, latest {latest}")


if __name__ == "__main__":
    main()
