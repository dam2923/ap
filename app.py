import os
from datetime import datetime, timezone
from flask import Flask, render_template, send_file, redirect, url_for, flash
from scan import run_scan

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_CSV = os.path.join(BASE_DIR, "agencypilot_tenants_cleaned.csv")

# Where we store the latest output (use Render persistent disk mount path)
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(BASE_DIR, "data"))
os.makedirs(DATA_DIR, exist_ok=True)

LATEST_CSV = os.path.join(DATA_DIR, "agencypilot_expiry_results_latest.csv")
LATEST_META = os.path.join(DATA_DIR, "latest_run.txt")

def read_last_run():
    if not os.path.exists(LATEST_META):
        return None
    with open(LATEST_META, "r", encoding="utf-8") as f:
        return f.read().strip()

def write_last_run(ts: str):
    with open(LATEST_META, "w", encoding="utf-8") as f:
        f.write(ts)

@app.get("/")
def index():
    last_run = read_last_run()
    has_csv = os.path.exists(LATEST_CSV)
    return render_template("index.html", last_run=last_run, has_csv=has_csv)

@app.post("/run")
def run_allowing_manual():
    # Basic safety: prevent multiple people hammering it at once
    lock_path = os.path.join(DATA_DIR, ".lock")
    if os.path.exists(lock_path):
        flash("A scan is already running. Try again in a minute.")
        return redirect(url_for("index"))

    try:
        open(lock_path, "w").close()
        out = run_scan(INPUT_CSV)
        out.to_csv(LATEST_CSV, index=False)

        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        write_last_run(ts)

        flash("Scan completed. You can download the latest CSV.")
        return redirect(url_for("index"))
    finally:
        if os.path.exists(lock_path):
            os.remove(lock_path)

@app.get("/download")
def download():
    if not os.path.exists(LATEST_CSV):
        flash("No results yet. Run a scan first.")
        return redirect(url_for("index"))
    return send_file(LATEST_CSV, as_attachment=True, download_name="agencypilot_expiry_results.csv")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "10000")))
