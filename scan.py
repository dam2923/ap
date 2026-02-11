import pandas as pd
import requests
import re
import time

DATE_RE = re.compile(
    r"licen[cs]e\s+will\s+expire\s+on\s+(\d{1,2}-[A-Za-z]{3}-\d{4}).*?(\d+)\s+days\s+left",
    re.I | re.S
)

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AgencyPilotExpiryCheck/1.0)"}

def run_scan(input_csv_path: str, delay_seconds: float = 0.75, timeout_seconds: int = 8) -> pd.DataFrame:
    df = pd.read_csv(input_csv_path)

    results = []
    for subdomain in df["subdomain"]:
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

        results.append({
            "subdomain": subdomain,
            "status": status,
            "expiry_date": expiry_date,
            "days_left": days_left,
            "url": url
        })

        time.sleep(delay_seconds)

    out = pd.DataFrame(results)

    # helpful sorting: expiring first, then errors, then no-banner
    out["sort_days"] = out["days_left"].fillna(10**9)
    out = out.sort_values(by=["sort_days", "status", "subdomain"]).drop(columns=["sort_days"])

    return out
