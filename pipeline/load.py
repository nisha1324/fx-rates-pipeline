"""Load: idempotent upsert into SQLite, plus a run log for auditing."""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

SCHEMA = """
CREATE TABLE IF NOT EXISTS fx_rates (
    date   TEXT NOT NULL,
    base   TEXT NOT NULL,
    quote  TEXT NOT NULL,
    rate   REAL NOT NULL CHECK (rate > 0),
    PRIMARY KEY (date, base, quote)
);
CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_at        TEXT NOT NULL,
    requested_from TEXT NOT NULL,
    rows_fetched  INTEGER NOT NULL,
    rows_new      INTEGER NOT NULL,
    latest_date   TEXT
);
"""


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    return conn


def latest_date(conn: sqlite3.Connection, base: str) -> str | None:
    row = conn.execute("SELECT MAX(date) FROM fx_rates WHERE base = ?", (base,)).fetchone()
    return row[0]


def upsert(conn: sqlite3.Connection, df: pd.DataFrame) -> int:
    """Insert new rows, overwrite changed ones; returns the number of new keys."""
    before = conn.execute("SELECT COUNT(*) FROM fx_rates").fetchone()[0]
    conn.executemany(
        "INSERT INTO fx_rates (date, base, quote, rate) VALUES (?, ?, ?, ?) "
        "ON CONFLICT(date, base, quote) DO UPDATE SET rate = excluded.rate",
        df[["date", "base", "quote", "rate"]].itertuples(index=False, name=None),
    )
    after = conn.execute("SELECT COUNT(*) FROM fx_rates").fetchone()[0]
    return after - before


def log_run(conn, requested_from: str, fetched: int, new: int, latest: str | None) -> None:
    conn.execute(
        "INSERT INTO pipeline_runs VALUES (?, ?, ?, ?, ?)",
        (datetime.now(timezone.utc).isoformat(timespec="seconds"),
         requested_from, fetched, new, latest),
    )
