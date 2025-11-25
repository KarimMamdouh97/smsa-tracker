import os
import requests
from bs4 import BeautifulSoup
import json

PUSHOVER_USER = os.environ["PUSHOVER_USER"]
PUSHOVER_TOKEN = os.environ["PUSHOVER_TOKEN"]
SMSA_URL = "https://www.smsaexpress.com/eg/trackingdetails?tracknumbers%5B0%5D=291541450756"
STATE_FILE = "state.json"

def push_message(event):
    message = (
        f"📦 <b>{event['status']}</b>\n"
        f"📍 {event['location']}\n"
        f"📅 {event['date']} @ {event['time']}"
    )

    requests.post("https://api.pushover.net/1/messages.json", data={
        "token": PUSHOVER_TOKEN,
        "user": PUSHOVER_USER,
        "title": "🚚 SMSA Shipment Update",
        "message": message,
        "html": 1,
        "priority": 0,
        "sound": "magic",
        "url": SMSA_URL,
        "url_title": "View Full Tracking"
    })


def parse_tracking():
    r = requests.get(SMSA_URL)
    soup = BeautifulSoup(r.text, "html.parser")

    ### === Main Shipment Status ===
    status_selector = "#ticket-tracking-details > div:nth-child(1) > div:nth-child(2) > div.col-xl-8.col-lg-8.col-md-8.col-sm-12 > div > div:nth-child(1) > p"
    status_el = soup.select_one(status_selector)
    shipment_status = status_el.get_text(strip=True) if status_el else None

    ### === Timeline Root ===
    timeline = soup.select_one(".tracking-timeline .tracking-details-container")
    if not timeline:
        return None

    ### === Latest Day ===
    first_day_row = timeline.select_one(".row")
    date_el = first_day_row.select_one(".date-wrap h4")
    date_text = date_el.get_text(strip=True) if date_el else ""

    ### === Latest Event (first trk-wrap) ===
    first_event = first_day_row.select_one(".tracking-details .trk-wrap")
    if not first_event:
        return None

    status_text = first_event.select_one("h4").get_text(strip=True)

    time_el = first_event.select_one(".trk-wrap-content-left span")
    time_text = time_el.get_text(strip=True) if time_el else ""

    loc_el = first_event.select_one(".trk-wrap-content-right span")
    loc_text = loc_el.get_text(strip=True) if loc_el else ""

    return {
        "shipment_status": shipment_status,
        "status": status_text,
        "time": time_text,
        "date": date_text,
        "location": loc_text
    }


def load_state():
    if not os.path.exists(STATE_FILE):
        return None
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


### ----- Main Logic -----
event = parse_tracking()
old = load_state()

# First run
if old is None and event:
    push_message(event)
    save_state(event)
    exit()

# Only notify if last event changed
if event and event != old:
    push_message(event)
    save_state(event)
