"""Extract: fetch daily reference rates from the Frankfurter API (ECB data, no key needed)."""
import time

import requests

from pipeline.config import API_URL, BASE, SYMBOLS


def fetch_range(start: str, end: str | None = None, base: str = BASE,
                symbols: list[str] = SYMBOLS, retries: int = 3) -> dict:
    """Return the raw JSON for a date range. `end=None` means "up to latest"."""
    url = f"{API_URL}/{start}..{end or ''}"
    params = {"base": base, "symbols": ",".join(symbols)}
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException:
            if attempt == retries:
                raise
            time.sleep(2 ** attempt)
