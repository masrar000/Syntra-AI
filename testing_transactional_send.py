# test_transactional_send.py
import os, json, requests
from dotenv import load_dotenv

# Load environment variables from .env in the current directory
load_dotenv()

token = os.getenv("HUBSPOT_PRIVATE_APP_TOKEN") or ""
email_id = os.getenv("HUBSPOT_EMAIL_TEMPLATE_ID") or ""

if not token:
    raise RuntimeError("HUBSPOT_PRIVATE_APP_TOKEN missing")
if not email_id.isdigit():
    raise RuntimeError("HUBSPOT_EMAIL_TEMPLATE_ID missing or not numeric")

url = "https://api.hubapi.com/marketing/v3/transactional/single-email/send"
payload = {
    "emailId": int(email_id),
    "customProperties": {"persona": "founder", "blogSlug": "ai-and-automation"},
    "message": {"to": "stage3.fics@gmail.com"}
}

r = requests.post(
    url,
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    data=json.dumps(payload),
    timeout=60,
)

print("STATUS:", r.status_code)
try:
    print("BODY:", json.dumps(r.json(), indent=2)[:800])
except Exception:
    print("BODY:", r.text[:800])
