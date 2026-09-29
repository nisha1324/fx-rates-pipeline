"""Transform: flatten the API payload into tidy rows and validate them."""
import pandas as pd


def to_rows(payload: dict, start: str | None = None) -> pd.DataFrame:
    """Nested {date: {ccy: rate}} -> one row per (date, base, quote, rate).

    The API snaps `start` back to the previous business day, so rows before
    `start` are dropped to keep loads strictly incremental.
    """
    rows = [
        {"date": d, "base": payload["base"], "quote": q, "rate": r}
        for d, quotes in payload.get("rates", {}).items()
        for q, r in quotes.items()
    ]
    df = pd.DataFrame(rows, columns=["date", "base", "quote", "rate"])
    if start is not None:
        df = df[df["date"] >= start]
    return df.sort_values(["date", "quote"]).reset_index(drop=True)


def validate(df: pd.DataFrame) -> pd.DataFrame:
    """Fail loudly on bad data instead of silently storing it."""
    problems = []
    if df[["date", "quote", "rate"]].isna().any().any():
        problems.append("null values")
    if (df["rate"] <= 0).any():
        problems.append("non-positive rates")
    if df.duplicated(["date", "base", "quote"]).any():
        problems.append("duplicate (date, base, quote) keys")
    try:
        pd.to_datetime(df["date"], format="%Y-%m-%d")
    except ValueError:
        problems.append("malformed dates")
    if problems:
        raise ValueError("Validation failed: " + ", ".join(problems))
    return df
