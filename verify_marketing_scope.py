import os, requests
from dotenv import load_dotenv

load_dotenv()
t = os.getenv("HUBSPOT_PRIVATE_APP_TOKEN") or ""
eid = os.getenv("HUBSPOT_EMAIL_TEMPLATE_ID") or ""
if not t: raise RuntimeError("HUBSPOT_PRIVATE_APP_TOKEN missing")
if not eid.isdigit(): raise RuntimeError("HUBSPOT_EMAIL_TEMPLATE_ID missing or not numeric")

u = f"https://api.hubapi.com/marketing/v3/emails/{eid}"
r = requests.get(u, headers={"Authorization": f"Bearer {t}", "Accept":"application/json"}, timeout=30)
print("STATUS:", r.status_code)
print(r.text[:600])
