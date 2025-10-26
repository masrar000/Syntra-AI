# # #THIS ALL IS LOCAL HOST!! UNCOMMENT IT AND RUN IT LOCALLY TO GET THE APP WORKING

# # # hubspot_client.py
# # # Minimal HubSpot helper for contacts, persona-based lists, and optional single-send.

# # # top of file


# # from __future__ import annotations

# # import os
# # import json
# # import time
# # import random
# # from typing import Dict, Any, List, Optional

# # import requests

# # # ===== Config =====
# # #BASE = "https://api.hubapi.com" #when running locally
# # BASE = os.getenv("HUBSPOT_API_BASE", "https://api.hubapi.com").rstrip("/")
# # HUB_TOKEN = os.getenv("HUBSPOT_PRIVATE_APP_TOKEN", "").strip()
# # SEND_ENABLED = os.getenv("HUBSPOT_SEND_ENABLED", "false").lower() == "true"
# # PERSONA_PROP = "audience_persona"

# # # UI persona keys → HubSpot enum values
# # _PERSONA_KEY_TO_VALUE = {
# #     "founder": "startup_founder",
# #     "creative": "creative_professional",
# #     "ops": "ops_manager",
# # }
# # _PERSONA_VALUE_TO_KEY = {v: k for k, v in _PERSONA_KEY_TO_VALUE.items()}


# # # ===== Internals =====
# # def _headers() -> Dict[str, str]:
# #     if not HUB_TOKEN:
# #         return {}
# #     return {"Authorization": f"Bearer {HUB_TOKEN}", "Content-Type": "application/json"}


# # def _req(method: str,path: str,*,params: Optional[Dict[str, Any]] = None,body: Optional[Dict[str, Any]] = None,timeout: int = 30) -> Dict[str, Any]:
# #     base = os.getenv("HUBSPOT_API_BASE", "https://api.hubapi.com")
# #     url = f"{BASE}{path}"
# #     # TEMP DEBUG
# #     print("HUBSPOT CALL:", method, url)
# #     resp = requests.request(method, url, headers=_headers(), params=params, json=body, timeout=timeout)
# #     if resp.status_code >= 300:
# #         try:
# #             detail = resp.json()
# #         except Exception:
# #             detail = resp.text
# #         raise RuntimeError(f"{method} {path} failed [{resp.status_code}] -> {detail}")
# #     try:
# #         return resp.json()
# #     except Exception:
# #         return {"status": "ok", "text": resp.text}


# # # ===== Capability flags =====
# # def hubspot_available() -> bool:
# #     return bool(HUB_TOKEN)


# # def can_send() -> bool:
# #     return hubspot_available() and SEND_ENABLED


# # # ===== Persona property management =====
# # def ensure_persona_property() -> Dict[str, Any]:
# #     """
# #     Ensure a contacts property named 'audience_persona' (enumeration) exists with three options.
# #     """
# #     if not hubspot_available():
# #         return {"status": "simulated", "property_name": PERSONA_PROP, "created": False, "note": "no HUBSPOT_PRIVATE_APP_TOKEN"}

# #     # Check if property exists
# #     r = requests.get(f"{BASE}/crm/v3/properties/contacts/{PERSONA_PROP}", headers=_headers(), timeout=30)
# #     if r.status_code == 200:
# #         return {"status": "ok", "property_name": PERSONA_PROP, "created": False}
# #     if r.status_code != 404:
# #         return {"status": "error", "code": r.status_code, "detail": r.text}

# #     # Create property
# #     body = {
# #         "name": PERSONA_PROP,
# #         "label": "Audience Persona",
# #         "type": "enumeration",
# #         "fieldType": "select",
# #         "groupName": "contactinformation",
# #         "options": [
# #             {"label": "Startup Founder", "value": "startup_founder"},
# #             {"label": "Creative Professional", "value": "creative_professional"},
# #             {"label": "Operations Manager", "value": "ops_manager"},
# #         ],
# #         "description": "Audience persona for targeted newsletters.",
# #         "hidden": False,
# #     }
# #     cr = requests.post(f"{BASE}/crm/v3/properties/contacts", headers=_headers(), json=body, timeout=30)
# #     if cr.status_code >= 300:
# #         try:
# #             detail = cr.json()
# #         except Exception:
# #             detail = cr.text
# #         return {"status": "error", "code": cr.status_code, "detail": detail}
# #     return {"status": "ok", "property_name": PERSONA_PROP, "created": True}

# # def init_crm() -> None:
# #     """Best-effort setup: ensure custom persona contact property exists."""
# #     try:
# #         ensure_persona_property()
# #     except Exception:
# #         pass

# # def _find_contact_id_by_email(email: str) -> Optional[str]:
# #     if not hubspot_available():
# #         return None
# #     body = {
# #         "filterGroups": [{"filters": [{"propertyName": "email", "operator": "EQ", "value": email}]}],
# #         "properties": ["email"]
# #     }
# #     res = _req("POST", "/crm/v3/objects/contacts/search", body=body)
# #     hits = res.get("results") or []
# #     return hits[0]["id"] if hits else None

# # def create_contact_note(email: str, text: str) -> Dict[str, Any]:
# #     """
# #     Create a Note and associate it to the contact found by email,
# #     so it shows on the contact timeline in HubSpot.
# #     """
# #     if not hubspot_available():
# #         return {"status": "simulated", "email": email, "note": text}

# #     contact_id = _find_contact_id_by_email(email)
# #     if not contact_id:
# #         return {"status": "error", "detail": f"Contact not found for {email}"}

# #     # HubSpot requires hs_timestamp (milliseconds since epoch)
# #     ts_ms = int(time.time() * 1000)

# #     body = {
# #         "properties": {
# #             "hs_note_body": text,
# #             "hs_timestamp": ts_ms,
# #         },
# #         "associations": [
# #             {
# #                 "to": {"id": contact_id},
# #                 # 202 = Note → Contact (HubSpot-defined association)
# #                 "types": [
# #                     {"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 202}
# #                 ],
# #             }
# #         ],
# #     }
# #     return _req("POST", "/crm/v3/objects/notes", body=body)




# # def _map_persona_key_to_value(x: str) -> str:
# #     return _PERSONA_KEY_TO_VALUE.get(x, x)


# # def _map_persona_value_to_key(x: str) -> str:
# #     return _PERSONA_VALUE_TO_KEY.get(x, x)


# # # ===== Contacts =====
# # def upsert_contact(email: str, properties: Dict[str, Any]) -> Dict[str, Any]:
# #     """
# #     True upsert by email using idProperty=email.
# #     Accepts 'persona' as founder|creative|ops and maps to PERSONA_PROP.
# #     """
# #     props = dict(properties or {})
# #     if "persona" in props:
# #         props[PERSONA_PROP] = _map_persona_key_to_value(props.pop("persona"))
# #     if "hs_persona" in props:
# #         props[PERSONA_PROP] = props.pop("hs_persona")

# #     if not hubspot_available():
# #         return {"status": "simulated", "email": email, "properties": {"email": email, **props}}

# #     payload = {"properties": {"email": email, **props}}

# #     # Try update
# #     update = requests.patch(
# #         f"{BASE}/crm/v3/objects/contacts/{email}",
# #         headers=_headers(),
# #         params={"idProperty": "email"},
# #         json=payload,
# #         timeout=30,
# #     )
# #     if update.status_code == 404:
# #         # Create
# #         create = requests.post(f"{BASE}/crm/v3/objects/contacts", headers=_headers(), json=payload, timeout=30)
# #         if create.status_code >= 300:
# #             try:
# #                 detail = create.json()
# #             except Exception:
# #                 detail = create.text
# #             return {"status": "error", "code": create.status_code, "detail": detail}
# #         return {"status": "ok", **create.json()}

# #     if update.status_code >= 300:
# #         try:
# #             detail = update.json()
# #         except Exception:
# #             detail = update.text
# #         return {"status": "error", "code": update.status_code, "detail": detail}

# #     return {"status": "ok", **update.json()}


# # def search_contacts_by_persona(persona_value_or_key: str, limit: int = 100) -> Dict[str, Any]:
# #     """
# #     Returns contacts where PERSONA_PROP equals the given value.
# #     Accepts either UI key (founder|creative|ops) or the enum value.
# #     """
# #     persona_value = _map_persona_key_to_value(persona_value_or_key)

# #     if not hubspot_available():
# #         return {"status": "simulated", "count": 1, "results": [{"email": f"sim_{persona_value}@example.com", "persona": persona_value}]}

# #     body = {
# #         "filterGroups": [{
# #             "filters": [{
# #                 "propertyName": PERSONA_PROP,
# #                 "operator": "EQ",
# #                 "value": persona_value
# #             }]
# #         }],
# #         "properties": ["email", "firstname", "lastname", PERSONA_PROP],
# #         "limit": limit
# #     }
# #     res = _req("POST", "/crm/v3/objects/contacts/search", body=body)
# #     items = []
# #     for r in res.get("results", []):
# #         p = r.get("properties", {}) or {}
# #         items.append({
# #             "id": r.get("id"),
# #             "email": p.get("email"),
# #             "firstname": p.get("firstname"),
# #             "lastname": p.get("lastname"),
# #             "persona": _map_persona_value_to_key(p.get(PERSONA_PROP, "")),
# #         })
# #     return {"status": "ok", "count": len(items), "results": items}


# # # ===== Segments / Lists =====
# # def ensure_persona_list(persona_key: str) -> Dict[str, Any]:
# #     """
# #     Ensure a persona-based list exists. Simulates by default.
# #     If token is present, attempts Lists API create/find with a dynamic filter on PERSONA_PROP.
# #     """
# #     list_name = f"[Auto] Persona: {persona_key}"
# #     persona_value = _map_persona_key_to_value(persona_key)

# #     if not hubspot_available():
# #         return {"status": "simulated", "list_id": f"sim-list-{persona_key}", "name": list_name}

# #     try:
# #         # Try to find an existing list
# #         lists = _req("GET", "/crm/v3/lists", params={"limit": 100})
# #         for lst in (lists.get("results") or []):
# #             if lst.get("name") == list_name:
# #                 return {"status": "ok", "list_id": lst.get("listId") or lst.get("id"), "name": list_name, "created": False}

# #         # Create a dynamic list filtered by persona
# #         body = {
# #             "name": list_name,
# #             "dynamic": True,
# #             "filterBranch": {
# #                 "filterBranchOperator": "AND",
# #                 "filters": [{
# #                     "property": PERSONA_PROP,
# #                     "operator": "EQ",
# #                     "value": persona_value
# #                 }]
# #             }
# #         }
# #         created = _req("POST", "/crm/v3/lists", body=body, timeout=30)
# #         return {"status": "ok", "list_id": created.get("listId") or created.get("id"), "name": list_name, "created": True}
# #     except Exception as e:
# #         return {"status": "simulated", "list_id": f"sim-list-{persona_key}", "name": list_name, "note": f"{type(e).__name__}: {e}"}

# # def single_send_marketing_email(email_id, to_addresses, custom_props=None):
# #     """
# #     Send a published 'Single send API' marketing email via v4.
# #     HubSpot expects one recipient per call.
# #     """
# #     if not can_send():
# #         sim_id = f"SIM-{int(time.time())}-{random.randint(1000, 9999)}"
# #         return {"mode": "simulate", "messageId": sim_id, "to": to_addresses,
# #                 "emailId": email_id, "props": custom_props or {}}

# #     eid = int(email_id) if str(email_id).isdigit() else int(os.getenv("HUBSPOT_EMAIL_TEMPLATE_ID"))

# #     results = []
# #     for addr in to_addresses:
# #         body = {
# #             "emailId": eid,
# #             "message": {"to": addr},  # single string, not a list
# #             "customProperties": custom_props or {},
# #         }
# #         res = _req("POST", "/marketing/v4/email/single-send", body=body, timeout=60)
# #         results.append({"to": addr, "response": res})
# #     return {"mode": "send", "results": results}



# # # ===== Local logging =====
# # def log_send_event(path: str, record: Dict[str, Any]) -> None:
# #     os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
# #     with open(path, "a", encoding="utf-8") as f:
# #         f.write(json.dumps(record, ensure_ascii=False) + "\n")








# #THIS ALL IS WEB HOST!! UNCOMMENT IT AND RUN IT TO GET THE APP WORKING
# # hubspot_client.py
# # Minimal HubSpot helper for contacts, persona-based lists, and optional single-send.
# from __future__ import annotations

# import os
# import json
# import time
# import random
# from typing import Dict, Any, List, Optional

# import requests

# # ===== Config =====
# BASE = os.getenv("HUBSPOT_API_BASE", "https://api.hubapi.com").rstrip("/")

# HUB_TOKEN = os.getenv("HUBSPOT_PRIVATE_APP_TOKEN", "").strip()

# # Prefer OAuth token if available
# if os.getenv("HUBSPOT_AUTH_MODE", "").lower() == "oauth":
#     HUB_TOKEN = os.getenv("HUBSPOT_OAUTH_ACCESS_TOKEN", "").strip()

# SEND_ENABLED = os.getenv("HUBSPOT_SEND_ENABLED", "false").lower() == "true"
# PERSONA_PROP = "audience_persona"
# AUTH_MODE = (os.getenv("HUBSPOT_AUTH_MODE") or "private").strip().lower()

# # UI persona keys → HubSpot enum values
# _PERSONA_KEY_TO_VALUE = {
#     "founder": "startup_founder",
#     "creative": "creative_professional",
#     "ops": "ops_manager",
# }
# _PERSONA_VALUE_TO_KEY = {v: k for k, v in _PERSONA_KEY_TO_VALUE.items()}


# # ===== OAuth Helper =====
# def _oauth_access_token() -> str:
#     """
#     Exchanges refresh token for a short-lived access token.
#     Only used when HUBSPOT_AUTH_MODE=oauth (recommended for Streamlit Cloud).
#     """
#     cid = os.getenv("HUBSPOT_CLIENT_ID", "").strip()
#     csec = os.getenv("HUBSPOT_CLIENT_SECRET", "").strip()
#     rtok = os.getenv("HUBSPOT_REFRESH_TOKEN", "").strip()
#     if not (cid and csec and rtok):
#         raise RuntimeError("OAuth selected but HUBSPOT_CLIENT_ID/SECRET/REFRESH_TOKEN missing")

#     data = {
#         "grant_type": "refresh_token",
#         "client_id": cid,
#         "client_secret": csec,
#         "refresh_token": rtok,
#     }
#     r = requests.post("https://api.hubapi.com/oauth/v1/token", data=data, timeout=30)
#     if r.status_code != 200:
#         raise RuntimeError(f"OAuth token exchange failed [{r.status_code}] -> {r.text}")
#     return r.json()["access_token"]


# # ===== Internals =====
# def _headers() -> Dict[str, str]:
#     if AUTH_MODE == "oauth":
#         token = _oauth_access_token()
#         return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
#     # private app token path
#     if not HUB_TOKEN:
#         return {}
#     return {"Authorization": f"Bearer {HUB_TOKEN}", "Content-Type": "application/json"}


# def _req(method: str, path: str, *, params: Optional[Dict[str, Any]] = None,
#          body: Optional[Dict[str, Any]] = None, timeout: int = 30) -> Dict[str, Any]:
#     url = f"{BASE}{path}"
#     # TEMP: console trace
#     print("HUBSPOT CALL:", method, url)
#     resp = requests.request(method, url, headers=_headers(), params=params, json=body, timeout=timeout)
#     if resp.status_code >= 300:
#         try:
#             detail = resp.json()
#         except Exception:
#             detail = resp.text
#         raise RuntimeError(f"{method} {path} failed [{resp.status_code}] -> {detail}")
#     try:
#         return resp.json()
#     except Exception:
#         return {"status": "ok", "text": resp.text}


# # ===== Capability flags =====
# def hubspot_available() -> bool:
#     if AUTH_MODE == "oauth":
#         return bool(os.getenv("HUBSPOT_CLIENT_ID") and os.getenv("HUBSPOT_REFRESH_TOKEN"))
#     return bool(HUB_TOKEN)


# def can_send() -> bool:
#     return hubspot_available() and SEND_ENABLED


# # ===== Persona property management =====
# def ensure_persona_property() -> Dict[str, Any]:
#     """
#     Ensure a contacts property named 'audience_persona' (enumeration) exists with three options.
#     """
#     if not hubspot_available():
#         return {"status": "simulated", "property_name": PERSONA_PROP, "created": False, "note": "no auth"}

#     # Check if property exists
#     r = requests.get(f"{BASE}/crm/v3/properties/contacts/{PERSONA_PROP}", headers=_headers(), timeout=30)
#     if r.status_code == 200:
#         return {"status": "ok", "property_name": PERSONA_PROP, "created": False}
#     if r.status_code != 404:
#         return {"status": "error", "code": r.status_code, "detail": r.text}

#     # Create property
#     body = {
#         "name": PERSONA_PROP,
#         "label": "Audience Persona",
#         "type": "enumeration",
#         "fieldType": "select",
#         "groupName": "contactinformation",
#         "options": [
#             {"label": "Startup Founder", "value": "startup_founder"},
#             {"label": "Creative Professional", "value": "creative_professional"},
#             {"label": "Operations Manager", "value": "ops_manager"},
#         ],
#         "description": "Audience persona for targeted newsletters.",
#         "hidden": False,
#     }
#     cr = requests.post(f"{BASE}/crm/v3/properties/contacts", headers=_headers(), json=body, timeout=30)
#     if cr.status_code >= 300:
#         try:
#             detail = cr.json()
#         except Exception:
#             detail = cr.text
#         return {"status": "error", "code": cr.status_code, "detail": detail}
#     return {"status": "ok", "property_name": PERSONA_PROP, "created": True}


# def init_crm() -> None:
#     """Best-effort setup: ensure custom persona contact property exists."""
#     try:
#         ensure_persona_property()
#     except Exception:
#         pass


# # ===== Contacts =====
# def _find_contact_id_by_email(email: str) -> Optional[str]:
#     if not hubspot_available():
#         return None
#     body = {
#         "filterGroups": [{"filters": [{"propertyName": "email", "operator": "EQ", "value": email}]}],
#         "properties": ["email"]
#     }
#     res = _req("POST", "/crm/v3/objects/contacts/search", body=body)
#     hits = res.get("results") or []
#     return hits[0]["id"] if hits else None


# def upsert_contact(email: str, properties: Dict[str, Any]) -> Dict[str, Any]:
#     """
#     True upsert by email using idProperty=email.
#     Accepts 'persona' as founder|creative|ops and maps to PERSONA_PROP.
#     """
#     props = dict(properties or {})
#     if "persona" in props:
#         props[PERSONA_PROP] = _PERSONA_KEY_TO_VALUE.get(props.pop("persona"), "")
#     if "hs_persona" in props:
#         props[PERSONA_PROP] = props.pop("hs_persona")

#     if not hubspot_available():
#         return {"status": "simulated", "email": email, "properties": {"email": email, **props}}

#     payload = {"properties": {"email": email, **props}}

#     # Try update
#     update = requests.patch(
#         f"{BASE}/crm/v3/objects/contacts/{email}",
#         headers=_headers(),
#         params={"idProperty": "email"},
#         json=payload,
#         timeout=30,
#     )
#     if update.status_code == 404:
#         # Create
#         create = requests.post(f"{BASE}/crm/v3/objects/contacts", headers=_headers(), json=payload, timeout=30)
#         if create.status_code >= 300:
#             try:
#                 detail = create.json()
#             except Exception:
#                 detail = create.text
#             return {"status": "error", "code": create.status_code, "detail": detail}
#         return {"status": "ok", **create.json()}

#     if update.status_code >= 300:
#         try:
#             detail = update.json()
#         except Exception:
#             detail = update.text
#         return {"status": "error", "code": update.status_code, "detail": detail}

#     return {"status": "ok", **update.json()}


# def search_contacts_by_persona(persona_value_or_key: str, limit: int = 100) -> Dict[str, Any]:
#     """
#     Returns contacts where PERSONA_PROP equals the given value.
#     Accepts either UI key (founder|creative|ops) or the enum value.
#     """
#     persona_value = _PERSONA_KEY_TO_VALUE.get(persona_value_or_key, persona_value_or_key)

#     if not hubspot_available():
#         return {"status": "simulated", "count": 1, "results": [{"email": f"sim_{persona_value}@example.com", "persona": persona_value}]}

#     body = {
#         "filterGroups": [{
#             "filters": [{
#                 "propertyName": PERSONA_PROP,
#                 "operator": "EQ",
#                 "value": persona_value
#             }]
#         }],
#         "properties": ["email", "firstname", "lastname", PERSONA_PROP],
#         "limit": limit
#     }
#     res = _req("POST", "/crm/v3/objects/contacts/search", body=body)
#     items = []
#     for r in res.get("results", []):
#         p = r.get("properties", {}) or {}
#         items.append({
#             "id": r.get("id"),
#             "email": p.get("email"),
#             "firstname": p.get("firstname"),
#             "lastname": p.get("lastname"),
#             "persona": _PERSONA_VALUE_TO_KEY.get(p.get(PERSONA_PROP, ""), ""),
#         })
#     return {"status": "ok", "count": len(items), "results": items}


# # ===== Segments / Lists =====
# def ensure_persona_list(persona_key: str) -> Dict[str, Any]:
#     """
#     Ensure a persona-based list exists. Simulates by default.
#     If token is present, attempts Lists API create/find with a dynamic filter on PERSONA_PROP.
#     """
#     list_name = f"[Auto] Persona: {persona_key}"
#     persona_value = _PERSONA_KEY_TO_VALUE.get(persona_key, persona_key)

#     if not hubspot_available():
#         return {"status": "simulated", "list_id": f"sim-list-{persona_key}", "name": list_name}

#     try:
#         lists = _req("GET", "/crm/v3/lists", params={"limit": 100})
#         for lst in (lists.get("results") or []):
#             if lst.get("name") == list_name:
#                 return {"status": "ok", "list_id": lst.get("listId") or lst.get("id"), "name": list_name, "created": False}

#         body = {
#             "name": list_name,
#             "dynamic": True,
#             "filterBranch": {
#                 "filterBranchOperator": "AND",
#                 "filters": [{
#                     "property": PERSONA_PROP,
#                     "operator": "EQ",
#                     "value": persona_value
#                 }]
#             }
#         }
#         created = _req("POST", "/crm/v3/lists", body=body, timeout=30)
#         return {"status": "ok", "list_id": created.get("listId") or created.get("id"), "name": list_name, "created": True}
#     except Exception as e:
#         return {"status": "simulated", "list_id": f"sim-list-{persona_key}", "name": list_name, "note": f"{type(e).__name__}: {e}"}


# # ===== Single-send =====
# def single_send_marketing_email(email_id, to_addresses, custom_props=None):
#     """
#     Send a published 'Single send API' marketing email via v4.
#     HubSpot expects one recipient per call.
#     """
#     if not can_send():
#         sim_id = f"SIM-{int(time.time())}-{random.randint(1000, 9999)}"
#         return {"mode": "simulate", "messageId": sim_id, "to": to_addresses,
#                 "emailId": email_id, "props": custom_props or {}}

#     eid = int(email_id) if str(email_id).isdigit() else int(os.getenv("HUBSPOT_EMAIL_TEMPLATE_ID"))

#     results = []
#     for addr in to_addresses:
#         body = {
#             "emailId": eid,
#             "message": {"to": addr},  # single string, not a list
#             "customProperties": custom_props or {},
#         }
#         res = _req("POST", "/marketing/v4/email/single-send", body=body, timeout=60)
#         results.append({"to": addr, "response": res})
#     return {"mode": "send", "results": results}


# # ===== Local logging =====
# def log_send_event(path: str, record: Dict[str, Any]) -> None:
#     os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
#     with open(path, "a", encoding="utf-8") as f:
#         f.write(json.dumps(record, ensure_ascii=False) + "\n")









# hubspot_client.py — Cloud-ready (Private token or OAuth)
from __future__ import annotations

import os
import json
import time
import random
from typing import Dict, Any, List, Optional

import requests

# ===== Config =====
BASE = os.getenv("HUBSPOT_API_BASE", "https://api.hubapi.com").rstrip("/")

# Auth mode: "private" (default) or "oauth"
AUTH_MODE = (os.getenv("HUBSPOT_AUTH_MODE") or "private").strip().lower()

# Private app token path (used when AUTH_MODE != "oauth")
HUB_TOKEN = os.getenv("HUBSPOT_PRIVATE_APP_TOKEN", "").strip()

# Sending gate
SEND_ENABLED = os.getenv("HUBSPOT_SEND_ENABLED", "false").lower() == "true"

# Persona custom property key
PERSONA_PROP = "audience_persona"

# UI persona keys → HubSpot enum values
_PERSONA_KEY_TO_VALUE = {
    "founder": "startup_founder",
    "creative": "creative_professional",
    "ops": "ops_manager",
}
_PERSONA_VALUE_TO_KEY = {v: k for k, v in _PERSONA_KEY_TO_VALUE.items()}

# ===== OAuth Helper =====
def _oauth_access_token() -> str:
    """
    Exchanges refresh token for a short-lived access token.
    Used when HUBSPOT_AUTH_MODE=oauth. Env vars required:
      - HUBSPOT_CLIENT_ID
      - HUBSPOT_CLIENT_SECRET
      - HUBSPOT_REFRESH_TOKEN
    """
    cid = os.getenv("HUBSPOT_CLIENT_ID", "").strip()
    csec = os.getenv("HUBSPOT_CLIENT_SECRET", "").strip()
    rtok = os.getenv("HUBSPOT_REFRESH_TOKEN", "").strip()
    if not (cid and csec and rtok):
      raise RuntimeError("OAuth selected but HUBSPOT_CLIENT_ID/SECRET/REFRESH_TOKEN missing")

    data = {
        "grant_type": "refresh_token",
        "client_id": cid,
        "client_secret": csec,
        "refresh_token": rtok,
    }
    r = requests.post("https://api.hubapi.com/oauth/v1/token", data=data, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"OAuth token exchange failed [{r.status_code}] -> {r.text}")
    return r.json()["access_token"]

# ===== Internals =====
def _headers() -> Dict[str, str]:
    if AUTH_MODE == "oauth":
        token = _oauth_access_token()
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    # private app token path
    if not HUB_TOKEN:
        return {}
    return {"Authorization": f"Bearer {HUB_TOKEN}", "Content-Type": "application/json"}

def _req(
    method: str,
    path: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    body: Optional[Dict[str, Any]] = None,
    timeout: int = 30,
) -> Dict[str, Any]:
    url = f"{BASE}{path}"
    print("HUBSPOT CALL:", method, url)
    resp = requests.request(method, url, headers=_headers(), params=params, json=body, timeout=timeout)
    if resp.status_code >= 300:
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text
        raise RuntimeError(f"{method} {path} failed [{resp.status_code}] -> {detail}")
    try:
        return resp.json()
    except Exception:
        return {"status": "ok", "text": resp.text}

# ===== Capability flags =====
def hubspot_available() -> bool:
    if AUTH_MODE == "oauth":
        return bool(os.getenv("HUBSPOT_CLIENT_ID") and os.getenv("HUBSPOT_REFRESH_TOKEN"))
    return bool(HUB_TOKEN)

def can_send() -> bool:
    return hubspot_available() and SEND_ENABLED

# ===== Persona property management =====
def ensure_persona_property() -> Dict[str, Any]:
    """
    Ensure a contacts property named 'audience_persona' (enumeration) exists with three options.
    If missing scopes, we fall back without failing app boot.
    """
    if not hubspot_available():
        return {"status": "simulated", "property_name": PERSONA_PROP, "created": False, "note": "no auth"}

    r = requests.get(f"{BASE}/crm/v3/properties/contacts/{PERSONA_PROP}", headers=_headers(), timeout=30)
    if r.status_code == 200:
        return {"status": "ok", "property_name": PERSONA_PROP, "created": False}
    if r.status_code != 404:
        return {"status": "error", "code": r.status_code, "detail": r.text}

    body = {
        "name": PERSONA_PROP,
        "label": "Audience Persona",
        "type": "enumeration",
        "fieldType": "select",
        "groupName": "contactinformation",
        "options": [
            {"label": "Startup Founder", "value": "startup_founder"},
            {"label": "Creative Professional", "value": "creative_professional"},
            {"label": "Operations Manager", "value": "ops_manager"},
        ],
        "description": "Audience persona for targeted newsletters.",
        "hidden": False,
    }
    cr = requests.post(f"{BASE}/crm/v3/properties/contacts", headers=_headers(), json=body, timeout=30)
    if cr.status_code >= 300:
        try:
            detail = cr.json()
        except Exception:
            detail = cr.text
        return {"status": "error", "code": cr.status_code, "detail": detail}
    return {"status": "ok", "property_name": PERSONA_PROP, "created": True}

def init_crm() -> None:
    try:
        ensure_persona_property()
    except Exception:
        pass

# ===== Contacts =====
def _find_contact_id_by_email(email: str) -> Optional[str]:
    if not hubspot_available():
        return None
    body = {
        "filterGroups": [{"filters": [{"propertyName": "email", "operator": "EQ", "value": email}]}],
        "properties": ["email"],
    }
    res = _req("POST", "/crm/v3/objects/contacts/search", body=body)
    hits = res.get("results") or []
    return hits[0]["id"] if hits else None

def upsert_contact(email: str, properties: Dict[str, Any]) -> Dict[str, Any]:
    """
    True upsert by email using idProperty=email.
    Accepts 'persona' as founder|creative|ops and maps to PERSONA_PROP.
    """
    props = dict(properties or {})
    if "persona" in props:
        props[PERSONA_PROP] = _PERSONA_KEY_TO_VALUE.get(props.pop("persona"), "")
    if "hs_persona" in props:
        props[PERSONA_PROP] = props.pop("hs_persona")

    if not hubspot_available():
        return {"status": "simulated", "email": email, "properties": {"email": email, **props}}

    payload = {"properties": {"email": email, **props}}

    update = requests.patch(
        f"{BASE}/crm/v3/objects/contacts/{email}",
        headers=_headers(),
        params={"idProperty": "email"},
        json=payload,
        timeout=30,
    )
    if update.status_code == 404:
        create = requests.post(f"{BASE}/crm/v3/objects/contacts", headers=_headers(), json=payload, timeout=30)
        if create.status_code >= 300:
            try:
                detail = create.json()
            except Exception:
                detail = create.text
            return {"status": "error", "code": create.status_code, "detail": detail}
        return {"status": "ok", **create.json()}

    if update.status_code >= 300:
        try:
            detail = update.json()
        except Exception:
            detail = update.text
        return {"status": "error", "code": update.status_code, "detail": detail}

    return {"status": "ok", **update.json()}

def search_contacts_by_persona(persona_value_or_key: str, limit: int = 100) -> Dict[str, Any]:
    """
    Return contacts where PERSONA_PROP equals the given value.
    Accepts either UI key (founder|creative|ops) or the enum value.
    """
    persona_value = _PERSONA_KEY_TO_VALUE.get(persona_value_or_key, persona_value_or_key)

    if not hubspot_available():
        return {
            "status": "simulated",
            "count": 1,
            "results": [{"email": f"sim_{persona_value}@example.com", "persona": persona_value}],
        }

    body = {
        "filterGroups": [{"filters": [{"propertyName": PERSONA_PROP, "operator": "EQ", "value": persona_value}]}],
        "properties": ["email", "firstname", "lastname", PERSONA_PROP],
        "limit": limit,
    }
    res = _req("POST", "/crm/v3/objects/contacts/search", body=body)
    items = []
    for r in res.get("results", []):
        p = r.get("properties", {}) or {}
        items.append(
            {
                "id": r.get("id"),
                "email": p.get("email"),
                "firstname": p.get("firstname"),
                "lastname": p.get("lastname"),
                "persona": _PERSONA_VALUE_TO_KEY.get(p.get(PERSONA_PROP, ""), ""),
            }
        )
    return {"status": "ok", "count": len(items), "results": items}

# ===== Segments / Lists =====
def ensure_persona_list(persona_key: str) -> Dict[str, Any]:
    """
    Ensure a persona-based dynamic list exists (or simulate if no auth).
    """
    list_name = f"[Auto] Persona: {persona_key}"
    persona_value = _PERSONA_KEY_TO_VALUE.get(persona_key, persona_key)

    if not hubspot_available():
        return {"status": "simulated", "list_id": f"sim-list-{persona_key}", "name": list_name}

    try:
        lists = _req("GET", "/crm/v3/lists", params={"limit": 100})
        for lst in (lists.get("results") or []):
            if lst.get("name") == list_name:
                return {"status": "ok", "list_id": lst.get("listId") or lst.get("id"), "name": list_name, "created": False}

        body = {
            "name": list_name,
            "dynamic": True,
            "filterBranch": {
                "filterBranchOperator": "AND",
                "filters": [{"property": PERSONA_PROP, "operator": "EQ", "value": persona_value}],
            },
        }
        created = _req("POST", "/crm/v3/lists", body=body, timeout=30)
        return {"status": "ok", "list_id": created.get("listId") or created.get("id"), "name": list_name, "created": True}
    except Exception as e:
        return {
            "status": "simulated",
            "list_id": f"sim-list-{persona_key}",
            "name": list_name,
            "note": f"{type(e).__name__}: {e}",
        }

# ===== Single-send =====
def single_send_marketing_email(email_id, to_addresses, custom_props=None):
    """
    Send a published 'Single send API' marketing email via v4.
    HubSpot expects one recipient per call.
    Requires: marketing-email scope, a Published Single Send email, and SEND_ENABLED=true.
    """
    if not can_send():
        sim_id = f"SIM-{int(time.time())}-{random.randint(1000, 9999)}"
        return {
            "mode": "simulate",
            "messageId": sim_id,
            "to": to_addresses,
            "emailId": email_id,
            "props": custom_props or {},
        }

    eid = int(email_id) if str(email_id).isdigit() else int(os.getenv("HUBSPOT_EMAIL_TEMPLATE_ID"))

    results = []
    for addr in to_addresses:
        body = {
            "emailId": eid,
            "message": {"to": addr},  # single string, not a list
            "customProperties": custom_props or {},
        }
        res = _req("POST", "/marketing/v4/email/single-send", body=body, timeout=60)
        results.append({"to": addr, "response": res})
    return {"mode": "send", "results": results}

# ===== Local logging =====
def log_send_event(path: str, record: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
