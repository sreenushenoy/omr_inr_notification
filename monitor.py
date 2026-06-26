import os
import json
import urllib.request
import urllib.error
from datetime import datetime

RESEND_API_KEY = os.environ["RESEND_API_KEY"]
ALERT_EMAIL = os.environ["ALERT_EMAIL"]
RATE_FILE = "last_rate.json"

def get_omr_inr_rate():
    url = "https://api.exchangerate-api.com/v4/latest/OMR"
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read())
        return data["rates"]["INR"]

def load_last_rate():
    if os.path.exists(RATE_FILE):
        with open(RATE_FILE, "r") as f:
            return json.load(f).get("rate")
    return None

def save_rate(rate):
    with open(RATE_FILE, "w") as f:
        json.dump({"rate": rate, "timestamp": datetime.utcnow().isoformat()}, f)

def send_email(current_rate, last_rate):
    subject = f"📈 OMR/INR Rate Alert: {current_rate:.4f}"
    body = f"""
    <h2>OMR → INR Rate Increased! 📈</h2>
    <p><strong>Current Rate:</strong> 1 OMR = {current_rate:.4f} INR</p>
    <p><strong>Previous Rate:</strong> 1 OMR = {last_rate:.4f} INR</p>
    <p><strong>Change:</strong> +{(current_rate - last_rate):.4f} INR</p>
    <p><strong>Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</p>
    <br>
    <p style="color:gray;font-size:12px;">This is an automated alert from your OMR/INR monitor.</p>
    """

    payload = json.dumps({
        "from": "OMR Alert <onboarding@resend.dev>",
        "to": [ALERT_EMAIL],
        "subject": subject,
        "html": body
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    with urllib.request.urlopen(req) as response:
        print(f"Email sent! Status: {response.status}")

def main():
    print(f"Checking OMR/INR rate at {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}...")

    current_rate = get_omr_inr_rate()
    print(f"Current rate: 1 OMR = {current_rate:.4f} INR")

    last_rate = load_last_rate()
    print(f"Last rate: {last_rate}")

    if last_rate is None:
        print("No previous rate found. Saving current rate as baseline.")
        save_rate(current_rate)
    elif current_rate > last_rate:
        print(f"Rate increased! {last_rate:.4f} → {current_rate:.4f}. Sending alert...")
        send_email(current_rate, last_rate)
        save_rate(current_rate)
    else:
        print(f"Rate has not increased ({last_rate:.4f} → {current_rate:.4f}). No alert sent.")
        save_rate(current_rate)

if __name__ == "__main__":
    main()
