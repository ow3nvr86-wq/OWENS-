#!/usr/bin/env python3
"""Fetch the latest price of every US-listed stock and ETF into one JSON file.

Used by .github/workflows/update-prices.yml to feed Paper Portfolio.
Standard library only, so the workflow needs no install step.

Output shape (kept compact because it holds ~10,000 rows):
  {"asOf": ISO-8601 UTC, "n": row count,
   "cols": ["s","n","p","c","t","m","y","x"],
   "rows": [[symbol, name, price, day change %, type, market cap $B, 1-year %, sector], ...]}
type is "S" for a stock and "E" for an ETF. Missing numbers are null.
"""
import datetime as dt
import gzip
import json
import re
import sys
import time
import urllib.request

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/128.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip",
    "Origin": "https://www.nasdaq.com",
    "Referer": "https://www.nasdaq.com/",
}
STOCKS = "https://api.nasdaq.com/api/screener/stocks?tableonly=true&download=true"
ETFS = "https://api.nasdaq.com/api/screener/etf?tableonly=true&download=true"
SYMBOL = re.compile(r"^[A-Z0-9][A-Z0-9.\-]{0,14}$")
NAME_TRIM = re.compile(
    r"\s+(Common Stock|Ordinary Shares|Class [A-C] (Common|Ordinary) (Stock|Shares)|"
    r"American Depositary Shares|Depositary Shares|Common Shares|Shares of Beneficial Interest)\b.*$",
    re.I,
)


def get_json(url, tries=3):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=60) as r:
                body = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    body = gzip.decompress(body)
                return json.loads(body)
        except Exception as e:  # network, HTTP or JSON error: retry
            last = e
            print(f"  attempt {i + 1} failed for {url}: {e}", file=sys.stderr)
            time.sleep(5 * (i + 1))
    raise RuntimeError(f"giving up on {url}: {last}")


def find_rows(obj):
    """Return the first list of dicts that carry a 'symbol' key, wherever it sits."""
    if isinstance(obj, list):
        if obj and isinstance(obj[0], dict) and "symbol" in obj[0]:
            return obj
        for v in obj:
            r = find_rows(v)
            if r:
                return r
    elif isinstance(obj, dict):
        for v in obj.values():
            r = find_rows(v)
            if r:
                return r
    return []


def num(v):
    if v is None:
        return None
    s = str(v).replace("$", "").replace(",", "").replace("%", "").strip()
    if s in ("", "NA", "N/A", "--", "-"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def pick(row, *keys):
    for k in keys:
        if row.get(k) not in (None, ""):
            return row[k]
    return None


def clean_symbol(s):
    # Nasdaq writes share classes with a slash (BRK/B); the app uses a dot.
    return str(s or "").strip().upper().replace("/", ".").replace("^", "-P")


def build(kind, rows, out):
    for r in rows:
        sym = clean_symbol(r.get("symbol"))
        price = num(pick(r, "lastsale", "lastSalePrice", "lastSale"))
        if not SYMBOL.match(sym) or not price or price <= 0:
            continue
        name = str(pick(r, "name", "companyName") or sym).strip()
        name = NAME_TRIM.sub("", name)[:60]
        pct = num(pick(r, "pctchange", "percentageChange"))
        mcap = num(r.get("marketCap"))
        one_year = num(r.get("oneYearPercentage"))
        sector = str(r.get("sector") or "").strip()[:30] or None
        out[sym] = [
            sym, name, round(price, 4),
            round(pct, 3) if pct is not None else None,
            kind,
            round(mcap / 1e9, 3) if mcap else None,
            round(one_year, 2) if one_year is not None else None,
            sector,
        ]


def main(path):
    out = {}
    stocks = find_rows(get_json(STOCKS))
    print(f"stocks: {len(stocks)} rows")
    build("S", stocks, out)
    try:
        etfs = find_rows(get_json(ETFS))
        print(f"etfs: {len(etfs)} rows")
        build("E", etfs, out)
    except RuntimeError as e:
        print(f"ETF list unavailable this run: {e}", file=sys.stderr)
    if len(out) < 2000:
        raise SystemExit(f"only {len(out)} symbols came back; refusing to publish a partial list")
    data = {
        "asOf": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "n": len(out),
        "cols": ["s", "n", "p", "c", "t", "m", "y", "x"],
        "rows": sorted(out.values()),
    }
    with open(path, "w") as f:
        json.dump(data, f, separators=(",", ":"))
    print(f"wrote {len(out)} symbols to {path}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "prices.json")
