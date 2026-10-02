"""Offline checks that the report SQL computes what it claims, on a tiny hand-made DB."""
import sqlite3

import pandas as pd

from pipeline.config import ROOT
from pipeline.load import SCHEMA
from report.build import ensure_math

SQL = ROOT / "sql"


def make_db(rows):
    conn = sqlite3.connect(":memory:")
    ensure_math(conn)
    conn.executescript(SCHEMA)
    conn.executemany("INSERT INTO fx_rates VALUES (?, 'AUD', ?, ?)", rows)
    return conn


def test_strength_pct_change():
    conn = make_db([("2024-01-02", "USD", 0.50), ("2024-06-03", "USD", 0.55)])
    df = pd.read_sql_query((SQL / "01_aud_strength.sql").read_text(), conn)
    assert df.loc[0, "pct_change"] == 10.0


def test_budget_variance_uses_previous_december():
    conn = make_db([("2023-12-01", "USD", 0.50), ("2024-01-02", "USD", 0.625)])
    df = pd.read_sql_query((SQL / "03_budget_variance.sql").read_text(), conn,
                           params={"usd_spend": 100_000})
    row = df.set_index("month").loc["2024-01"]
    # Budget 200,000 AUD vs actual 160,000 AUD: 40,000 saved.
    assert row["budget_rate"] == 0.5 and row["variance_aud"] == 40_000


def test_ensure_math_fallback_matches_python():
    import math
    conn = sqlite3.connect(":memory:")
    ensure_math(conn)
    ln, root = conn.execute("SELECT LN(2.0), SQRT(252)").fetchone()
    assert abs(ln - math.log(2.0)) < 1e-12 and abs(root - math.sqrt(252)) < 1e-12


def test_quarterly_policy_uses_month_before_quarter():
    conn = make_db([("2023-12-01", "USD", 0.50), ("2024-03-01", "USD", 0.80),
                    ("2024-05-01", "USD", 0.625)])
    df = pd.read_sql_query((SQL / "05_budget_policy.sql").read_text(), conn,
                           params={"usd_spend": 100_000}).set_index("month")
    may = df.loc["2024-05"]
    # Annual budget uses Dec (0.50), quarterly uses Mar (0.80); actual 0.625 -> 160,000 AUD.
    assert may["annual_error_aud"] == 40_000 and may["quarterly_error_aud"] == -35_000
