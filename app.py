import os
import io
from flask import Flask, render_template, send_file, flash
from scan import run_scan

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_CSV = os.path.join(BASE_DIR, "agencypilot_tenants_cleaned.csv")

@app.get("/")
def index():
    return render_template("index.html")

@app.post("/run")
def run_scan_and_download():
    # Run the scan
    out = run_scan(INPUT_CSV)

    # Create CSV in memory (Render Free: no persistent disk needed)
    csv_bytes = out.to_csv(index=False).encode("utf-8")
    buf = io.BytesIO(csv_bytes)

    return send_file(
        buf,
        as_attachment=True,
        download_name="agencypilot_expiry_results.csv",
        mimetype="text/csv"
    )

if __name__ == "__main__":
    # Render sets PORT; default here for local runs
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
