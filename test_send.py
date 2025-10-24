# test_send.py  (Marketing Single Send v4)
import os, json, requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("HUBSPOT_PRIVATE_APP_TOKEN")
email_id_str = os.getenv("HUBSPOT_EMAIL_TEMPLATE_ID")  # from the UI "You're all set..." panel

if not token:
    raise RuntimeError("HUBSPOT_PRIVATE_APP_TOKEN is not set. Check your .env.")
if not email_id_str:
    raise RuntimeError("HUBSPOT_EMAIL_TEMPLATE_ID is not set. Check your .env.")

email_id = int(email_id_str)

url = "https://api.hubapi.com/marketing/v4/email/single-send"
payload = {
    "emailId": email_id,
    "message": {
        "to": [{"email": "stage3.fics@gmail.com"}]  # use a test inbox you can check
        # you may add "replyTo": [{"email":"you@yourdomain.com"}]
    },
    # available in the email as {{ custom.persona }} and {{ custom.blogSlug }}
    "customProperties": {"persona": "founder", "blogSlug": "ai-and-automation"}
}

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)

print("STATUS:", r.status_code)
try:
    print("BODY:", json.dumps(r.json(), indent=2)[:1200])
except Exception:
    print("BODY:", r.text[:1200])
