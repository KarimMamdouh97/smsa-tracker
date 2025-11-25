import os
import json
import requests
from bs4 import BeautifulSoup
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==== CONFIG ====
PUSHOVER_USER = os.environ["PUSHOVER_USER"]
PUSHOVER_TOKEN = os.environ["PUSHOVER_TOKEN"]
SMSA_URL = "https://www.smsaexpress.com/eg/trackingdetails?tracknumbers%5B0%5D=291541450756"
STATE_FILE = "last_status.json"

# ==== HELPER: send Pushover notification ====
def send_notification(title, message):
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": PUSHOVER_TOKEN,  # your custom app token (defines logo)
            "user": PUSHOVER_USER,
            "title": title,
            "message": message,
        },
    )

# ==== HELPER: read last status ====
def read_last_status():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}

# ==== HELPER: save last status ====
def save_last_status(status):
    with open(STATE_FILE, "w") as f:
        json.dump(status, f)

# ==== PARSE TRACKING ====
def parse_tracking():
    r = requests.get(SMSA_URL, verify=False)
    soup = BeautifulSoup(r.text, "html.parser")

    # Latest status
    latest = soup.select_one(
        "#ticket-tracking-details > div:nth-child(1) > div:nth-child(2) > div.col-xl-8.col-lg-8.col-md-8.col-sm-12 > div > div:nth-child(1) > p"
    )
    # Optional: get location
    location_span = soup.select_one(
        "#ticket-tracking-details .tracking-details .trk-wrap-content-right span"
    )

    latest_status = latest.get_text(strip=True) if latest else "No status found"
    location = location_span.get_text(strip=True) if location_span else "Unknown"

    return f"{latest_status} 📍 {location}"

# ==== MAIN ====
if __name__ == "__main__":
    try:
        last_status = read_last_status()
        current_status = parse_tracking()

        if last_status.get("status") != current_status:
            send_notification("📦 SMSA Update", current_status)
            save_last_status({"status": current_status})
            print("✅ Notification sent:", current_status)
        else:
            print("ℹ️ No new update. Latest status:", current_status)

    except Exception as e:
        print("❌ Error:", e)
        exit(1)
