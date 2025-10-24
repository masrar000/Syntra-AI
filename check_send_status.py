# check_send_status.py
import os, requests, sys, json
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("HUBSPOT_PRIVATE_APP_TOKEN") or ""
status_id = sys.argv[1] if len(sys.argv) > 1 else ""

if not token: raise RuntimeError("HUBSPOT_PRIVATE_APP_TOKEN missing")
if not status_id: raise RuntimeError("Pass statusId as argv[1]")

u = f"https://api.hubapi.com/marketing/v3/email/send-statuses/{status_id}"
r = requests.get(u, headers={"Authorization": f"Bearer {token}"}, timeout=30)
print("STATUS:", r.status_code)
print(json.dumps(r.json(), indent=2) if r.headers.get("content-type","").startswith("application/json") else r.text)
