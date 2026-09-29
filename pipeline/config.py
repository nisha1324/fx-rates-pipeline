"""Pipeline settings: which currencies to track and where to store them."""
from pathlib import Path

API_URL = "https://api.frankfurter.dev/v1"
BASE = "AUD"
# Currencies an Australian business typically pays suppliers / earns revenue in.
SYMBOLS = ["USD", "EUR", "GBP", "CNY", "INR", "JPY", "NZD", "SGD"]
# First day of history to backfill on an empty database.
START_DATE = "2023-01-01"

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "fx_rates.db"
