import os, json, requests
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("HUBSPOT_PRIVATE_APP_TOKEN") or ""
email_id = os.getenv("HUBSPOT_EMAIL_TEMPLATE_ID") or ""

if not token:
    raise RuntimeError("HUBSPOT_PRIVATE_APP_TOKEN missing")
if not email_id.isdigit():
    raise RuntimeError("HUBSPOT_EMAIL_TEMPLATE_ID missing or not numeric")

url = "https://api.hubapi.com/marketing/v4/email/single-send"
payload = {
    "emailId": int(email_id),
    "message": {
        "to": "stage3.fics@gmail.com"   # change if you want
        # optional: "from": "Your Name <you@yourdomain.com>",
        # optional: "replyTo": ["you@yourdomain.com"]
    },
    # available in template as {{ custom.persona }} etc.
    "customProperties": {
        "persona": "founder",
        "blogSlug": "ai-and-automation"
    }
}

r = requests.post(
    url,
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    data=json.dumps(payload),
    timeout=60,
)
print("STATUS:", r.status_code)
try:
    print("BODY:", json.dumps(r.json(), indent=2)[:1000])
except Exception:
    print("BODY:", r.text[:1000])
