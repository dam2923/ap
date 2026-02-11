import pandas as pd
import requests
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

DATE_RE = re.compile(
    r"licen[cs]e\s+will\s+expire\s+on\s+(\d{1,2}-[A-Za-z]{3}-\d{4}).*?(\d+)\s+days\s+left",
    re.I | re.S
)

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AgencyPilotExpiryCheck/1.0)"}

def _check_one(subdomain: str, timeout_seconds: int):
    url = f"https://{subdomain}/"
    status = "no-banner"
    expiry_date = None
    days_left = None

    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout_seconds)
        m = DATE_RE.search(r.text)
        if m:
            status = "expiry-found"
            expiry_date = m.group(1)
            days_left = int(m.group(2))
    except Exception:
        status = "error"

    return {
        "subdomain": subdomain,
        "url": url,
        "status": status,
        "expiry_date": expiry_date,
        "days_left": days_left,
    }

def run_scan(input_csv_path: str, timeout_seconds: int = 6, max_workers: int = 25) -> pd.DataFrame:
    df = pd.read_csv(input_csv_path)
    subdomains = df["subdomain"].dropna().astype(str).tolist()

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = [ex.submit(_check_one, s, timeout_seconds) for s in subdomains]
        for f in as_completed(futures):
            results.append(f.result())

    out = pd.DataFrame(results)
    out["sort_days"] = out["days_left"].fillna(10**9)
    out = out.sort_values(by=["sort_days", "status", "subdomain"]).drop(columns=["sort_days"])
    return out
