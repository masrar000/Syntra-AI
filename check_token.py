import os, requests, json
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("HUBSPOT_PRIVATE_APP_TOKEN")
if not token:
    raise RuntimeError("HUBSPOT_PRIVATE_APP_TOKEN missing")

# HubSpot token introspection endpoint works for private app tokens
u = f"https://api.hubapi.com/oauth/v1/access-tokens/{token}"
r = requests.get(u, timeout=30)
print("STATUS:", r.status_code)
print("BODY:", r.text[:1200])

if r.ok:
    data = r.json()
    print("\nResolved portal (hub_id):", data.get("hub_id"))
    print("User:", data.get("user"))
    print("Scopes:", data.get("scopes"))
