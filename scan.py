import csv
import requests
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import StringIO

DATE_RE = re.compile(
    r"licen[cs]e\s+will\s+expire\s+on\s+(\d{1,2}-[A-Za-z]{3}-\d{4}).*?(\d+)\s+days\s+left",
    re.I | re.S
)

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AgencyPilotExpiryCheck/1.0)"}


def _check_one(subdomain: str, timeout_seconds: int):
    url = f"https://{subdomain}/"
    status = "no-banner"
    expiry_date = ""
    days_left = ""

    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout_seconds)
        m = DATE_RE.search(r.text)
        if m:
            status = "expiry-found"
            expiry_date = m.group(1)
            days_left = m.group(2)
    except Exception:
        status = "error"

    return {
        "subdomain": subdomain,
        "url": url,
        "status": status,
        "expiry_date": expiry_date,
        "days_left": days_left,
    }


def run_scan_csv(input_csv_path: str, timeout_seconds: int = 6, max_workers: int = 25) -> str:
    with open(input_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        subdomains = [row["subdomain"].strip() for row in reader if row.get("subdomain")]

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = [ex.submit(_check_one, s, timeout_seconds) for s in subdomains]
        for f in as_completed(futures):
            results.append(f.result())

    def sort_key(r):
        try:
            d = int(r["days_left"]) if r["days_left"] else 10**9
        except Exception:
            d = 10**9
        return (d, r["status"], r["subdomain"])

    results.sort(key=sort_key)

    output = StringIO()
    fieldnames = ["subdomain", "url", "status", "expiry_date", "days_left"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)
    return output.getvalue()
