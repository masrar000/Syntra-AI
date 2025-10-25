import os, requests, json
BASE = "https://api.hubapi.com"
t = os.environ["HUBSPOT_PRIVATE_APP_TOKEN"]
eid = int(os.environ["HUBSPOT_EMAIL_TEMPLATE_ID"])
to  = os.environ.get("TEST_TO","stage3.fics@gmail.com")

body = {"emailId": eid, "message": {"to": to}, "customProperties": {"ping":"pong"}}
r = requests.post(f"{BASE}/marketing/v4/email/single-send",
                  headers={"Authorization": f"Bearer {t}", "Content-Type":"application/json"},
                  json=body, timeout=60)
print("STATUS:", r.status_code)
print(r.text[:1200])
