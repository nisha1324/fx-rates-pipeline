"""Offline tests: no network, uses a sample payload shaped like the real API."""
import pandas as pd
import pytest

from pipeline.load import connect, latest_date, upsert
from pipeline.transform import to_rows, validate

PAYLOAD = {
    "amount": 1.0, "base": "AUD", "start_date": "2023-12-29", "end_date": "2024-01-03",
    "rates": {
        "2023-12-29": {"INR": 56.509, "USD": 0.67946},
        "2024-01-02": {"INR": 56.531, "USD": 0.67852},
        "2024-01-03": {"INR": 56.024, "USD": 0.67252},
    },
}


def test_to_rows_flattens_and_drops_snapped_start():
    df = to_rows(PAYLOAD, start="2024-01-01")
    assert len(df) == 4
    assert df["date"].min() == "2024-01-02"
    assert set(df.columns) == {"date", "base", "quote", "rate"}


@pytest.mark.parametrize("bad", [
    {"rate": -1.0}, {"rate": None}, {"date": "02/01/2024"},
])
def test_validate_rejects_bad_rows(bad):
    df = to_rows(PAYLOAD)
    for col, val in bad.items():
        df.loc[0, col] = val
    with pytest.raises(ValueError):
        validate(df)


def test_validate_rejects_duplicates():
    df = to_rows(PAYLOAD)
    with pytest.raises(ValueError):
        validate(pd.concat([df, df.head(1)]))


def test_upsert_is_idempotent(tmp_path):
    conn = connect(tmp_path / "t.db")
    df = validate(to_rows(PAYLOAD))
    assert upsert(conn, df) == 6
    assert upsert(conn, df) == 0          # re-running adds nothing
    assert latest_date(conn, "AUD") == "2024-01-03"
