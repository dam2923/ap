import os
import io
from flask import Flask, render_template, send_file
from scan import run_scan_csv

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_CSV = os.path.join(BASE_DIR, "agencypilot_tenants_cleaned.csv")


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/run")
def run_scan_and_download():
    csv_text = run_scan_csv(INPUT_CSV)
    buf = io.BytesIO(csv_text.encode("utf-8"))

    return send_file(
        buf,
        as_attachment=True,
        download_name="agencypilot_expiry_results.csv",
        mimetype="text/csv",
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
