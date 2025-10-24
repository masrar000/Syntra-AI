# AI Marketing Pipeline (Streamlit, HubSpot-ready)

A localhost Streamlit app that ideates a weekly blog, generates 3 persona-specific newsletters,
optionally pushes to HubSpot (contacts + lists + email single-send), and logs performance metrics
(open rate, click rate, unsubscribes) for historical comparison with an AI summary.

## What you get
- **Blog generator**, ~600 words, with multiple copy options.
- **Three newsletters** tailored to:
  - *Founders*: ROI and efficiency
  - *Creative professionals*: inspiration and time-saving
  - *Operations managers*: workflow, integration, stability
- **JSON storage** for blog + newsletters + send logs.
- **HubSpot integration** (optional): update contacts with persona, create segments (lists), and **attempt** sending via the Single-send API.
  - If scopes/subscription are missing, the app **falls back** to simulation-only mode and still logs everything.
- **Performance dashboard** with historical stats and an **AI-written performance summary**.

---

## 1) Prereqs

- Python 3.10+
- `pip install -r requirements.txt`
- Create a `.env` file in the project root (or set env vars some other way):

```
OPENAI_API_KEY=sk-...              # or use GEMINI_API_KEY if you prefer Gemini
LLM_PROVIDER=openai                 # options: openai or gemini
HUBSPOT_PRIVATE_APP_TOKEN=pat-...   # HubSpot Private App token, optional
HUBSPOT_SEND_ENABLED=false          # true to try API send, false to simulate
HUBSPOT_PORTAL_TIMEZONE=America/New_York
```

> If you don't set `HUBSPOT_PRIVATE_APP_TOKEN`, the app runs in full **simulation** mode.

Install and run:
```
pip install -r requirements.txt
streamlit run app.py
```

---

## 2) HubSpot setup, token, and scopes

HubSpot no longer uses legacy "API keys". Use a **Private App** to generate an access token. You must be a **Super Admin**.
Steps (summarized from HubSpot docs):
1. In HubSpot, go to **Settings → Integrations → Private Apps**.
2. Create a Private App, name it, set a logo if you like.
3. Under **Scopes**, select at minimum:
   - `crm.objects.contacts.read` and `crm.objects.contacts.write` (manage contacts),
   - `crm.lists.read` and `crm.lists.write` (segments/lists v3),
   - `marketing-email` (required for the **Single-send** marketing email API).
4. Save, then copy the **Access Token** into your `.env` as `HUBSPOT_PRIVATE_APP_TOKEN`.
   - Docs, scopes and single-send overview: developers.hubspot.com (see links in the app sidebar).

### Important notes
- The **Single-send API** sends marketing emails that are created as templates in the HubSpot marketing email tool. It requires the proper HubSpot **subscription/plan** and scope. Some portals cannot send marketing emails via API.
- If your portal lacks permissions or add-ons, the app will **simulate** sends rather than fail hard.
- You can still push persona updates to contacts and create segments, even if email sending is simulated.

---

## 3) Data model

- `data/content/{yyyymmdd}-{slug}.json`: holds blog + three newsletters + variants & metadata.
- `data/crm/send_log.jsonl`: one line per distribution event, including blog title, send datetime, audience, newsletter_id, hubspot_message_id (or SIM-...).
- `data/perf/metrics.jsonl`: aggregate metrics over time. Each run appends `{date, audience, open_rate, click_rate, unsub_rate}`.
- `data/perf/summary.json`: latest AI-written performance summary across audiences.

---

## 4) Personas & Segments

We use a **contact property** `persona` with values in {founder, creative, ops}. If you already have a property, map it in the app settings.
The app can create **segments/lists** for each persona using the Lists v3 API, then target those when sending (or simulating).

---

## 5) Limitations

- Real email sending requires supported plans and scopes. If unavailable, the app simulates and logs sends with `SIM-...` ids.
- Metrics collection is simulated unless you replace the simulator with HubSpot Analytics or Email Events API reads.

---

## 6) Extend
- Swap the LLM to Gemini by setting `LLM_PROVIDER=gemini` and `GEMINI_API_KEY`, the interface is already stubbed.
- Replace simulator with HubSpot analytics pulls and compute real historical comparisons.
- Add A/B testing by generating two newsletter variants per persona.
