"""
AI Marketing Pipeline runner
- Generates a blog + 3 persona newsletters with OpenAI (or a deterministic fallback).
- Pulls persona segments from HubSpot (via hubspot_client.py).
- Simulates sends + performance and writes a campaign artifact under ./runs/
"""

import os
import json
import time
import random
import pathlib
from typing import Dict, Any, List

from dotenv import load_dotenv
import hubspot_client as hc  #local helper

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except Exception:
    OPENAI_AVAILABLE = False

# environment and paths
load_dotenv(override=True)

RUNS_DIR = pathlib.Path("runs")
RUNS_DIR.mkdir(exist_ok=True)

# Read model id from env
# default to a broadly available model
MODEL_ID = (os.getenv("OPENAI_MODEL") or "gpt-3.5-turbo-0125").strip()


# OpenAI helpers
def get_openai_client():
    """
    Return an OpenAI client if API key is present
    else None.
    """
    if not OPENAI_AVAILABLE:
        return None
    key = (os.getenv("OPENAI_API_KEY") or "").strip().strip('"').strip("'")
    if not key:
        return None
    try:
        return OpenAI(api_key=key)
    except Exception:
        return None


def ai_or_fallback(prompt: str) -> str:
    """
    Use OpenAI if available and configured
    otherwise return a deterministic fallback.
    """
    client = get_openai_client()
    if not client:
        return f"[FAKE AI OUTPUT] {prompt[:140]}..."

    try:
        resp = client.chat.completions.create(
            model=MODEL_ID,
            messages=[
                {"role": "system", "content": "You are a concise marketing copywriter."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=500,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        # If the model isn't allowed or the call fails, fall back gracefully
        return f"[FAKE AI OUTPUT due to model/error: {e.__class__.__name__}] {prompt[:140]}..."


# Content generation
def generate_content(topic: str) -> Dict[str, Any]:
    """Generate a blog draft + persona-specific newsletters."""
    blog_prompt = (
        f"Create a short blog draft (400–600 words) about: '{topic}'.\n"
        "Include a title and 3–5 subheads. Audience: B2B SaaS leaders. Keep it practical."
    )
    blog = ai_or_fallback(blog_prompt)

    personas = {
        "startup_founder": "Early-stage founders focused on growth and speed",
        "creative_professional": "Design/creative agency leads who want client-friendly automation",
        "ops_manager": "Operations managers who care about reliability and workflows",
    }

    newsletters: Dict[str, str] = {}
    for persona_key, persona_desc in personas.items():
        nl_prompt = (
            f"Write a short newsletter (120–180 words) summarizing this blog for {persona_desc}.\n"
            f"Topic: '{topic}'. Include one actionable takeaway and a soft CTA to read the blog."
        )
        newsletters[persona_key] = ai_or_fallback(nl_prompt)

    return {"topic": topic, "blog": blog, "newsletters": newsletters}



# performance simulation

def simulate_performance() -> Dict[str, Any]:
    """
    Create realistic-looking engagement metrics.
    """
    open_rate = round(random.uniform(0.25, 0.55), 3)
    click_rate = round(random.uniform(0.03, 0.15), 3)
    unsub_rate = round(random.uniform(0.001, 0.01), 3)
    return {"open_rate": open_rate, "click_rate": click_rate, "unsubscribe_rate": unsub_rate}


def performance_summary(perf_by_segment: Dict[str, Any], topic: str) -> str:
    """
    Summarize metrics with OpenAI if available, otherwise fallback text.
    """
    client = get_openai_client()
    if client:
        bullet = "\n".join(
            f"- {seg}: open {m['open_rate']*100:.1f}%, click {m['click_rate']*100:.1f}%, "
            f"unsub {m['unsubscribe_rate']*100:.2f}%"
            for seg, m in perf_by_segment.items()
        )
        prompt = (
            f"Given this campaign topic: {topic}\n\n"
            f"Metrics by segment:\n{bullet}\n\n"
            "Write a 4–6 sentence marketing insights summary with 2 concrete next-step suggestions. Use that suggestion for the next topic."
        )
        try:
            resp = client.chat.completions.create(
                model=MODEL_ID,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=300,
            )
            return (resp.choices[0].message.content or "").strip()
        except Exception as e:
            pass  # fall back if the model isn't accessible

    # Fallback summary
    top = max(perf_by_segment.items(), key=lambda kv: kv[1]["click_rate"])[0]
    return (
        f"[FAKE SUMMARY] Best click-rate segment: {top}. Double down on messaging that segment values. "
        f"Test a stronger CTA next week and add a visual example for credibility."
    )



# Main pipeline
def main(topic: str):
    print(f"\n🧠 Generating AI marketing campaign for topic: {topic}\n")

    # 1) Generate content
    content = generate_content(topic)

    # 2) Pull segments (by your custom 'audience_persona' property via hubspot_client)
    segments = {
        "startup_founder": hc.search_contacts_by_persona("startup_founder"),
        "creative_professional": hc.search_contacts_by_persona("creative_professional"),
        "ops_manager": hc.search_contacts_by_persona("ops_manager"),
    }

    # 3) Simulated sends (real API call only if HUBSPOT_SEND_ENABLED=true)
    send_logs: List[Dict[str, Any]] = []
    for seg_key, res in segments.items():
        emails = [r["email"] for r in res.get("results", []) if r.get("email")]
        if not emails:
            continue

        email_template_id = os.getenv("HUBSPOT_EMAIL_TEMPLATE_ID", "TEMPLATE_ID")
        payload = hc.single_send_marketing_email(
            email_id=email_template_id,
            to_addresses=emails,
            custom_props={"persona_segment": seg_key, "topic": topic},
        )
        send_logs.append({"segment": seg_key, "result": payload, "emails": emails})

        # Local audit log
        hc.log_send_event(
            "runs/sends.log",
            {"ts": int(time.time()), "segment": seg_key, "emails": emails, "result": payload},
        )

    # 4) Simulate performance per segment & summarize
    perf = {seg: simulate_performance() for seg in segments.keys()}
    summary = performance_summary(perf, topic)

    # 5) Save a campaign artifact
    ts = time.strftime("%Y%m%d-%H%M%S")
    out = {
        "topic": topic,
        "content": content,
        "segments": {k: v.get("results", []) for k, v in segments.items()},
        "sends": send_logs,
        "performance": perf,
        "summary": summary,
        "model_used": MODEL_ID,
    }
    out_path = RUNS_DIR / f"campaign_{ts}.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"✅ Saved campaign ->  {out_path}\n")
    print("📊 Performance Summary:\n")
    print(summary)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print('Usage: python run_campaign.py "<topic>"')
        sys.exit(1)
    main(sys.argv[1])
