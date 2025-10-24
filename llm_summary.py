# llm_summary.py
import os
from typing import List, Dict, Any
from collections import defaultdict
from dotenv import load_dotenv

# Load .env for both CLI and Streamlit runs
load_dotenv(override=True)

PROVIDER = (os.getenv("LLM_PROVIDER") or "openai").strip().lower()
OPENAI_MODEL = (os.getenv("OPENAI_MODEL") or "gpt-3.5-turbo-0125").strip()
GEMINI_MODEL = (os.getenv("GEMINI_MODEL") or "gemini-1.5-flash").strip()


# OpenAI helpers
def _get_openai_client():
    try:
        from openai import OpenAI
    except Exception:
        return None
    key = (os.getenv("OPENAI_API_KEY") or "").strip().strip('"').strip("'")
    if not key:
        return None
    return OpenAI(api_key=key)


def _call_openai(prompt: str, system: str = "") -> str:
    client = _get_openai_client()
    if not client:
        return f"[FAKE AI OUTPUT] {prompt[:160]}..."

    msgs = [{"role": "system", "content": system}] if system else []
    msgs.append({"role": "user", "content": prompt})

    try:
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=msgs,
            temperature=0.4,
            max_tokens=600,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        return f"[FAKE AI OUTPUT due to error: {e}] {prompt[:160]}..."


# Gemini helpers
def _call_gemini(prompt: str, system: str = "") -> str:
    try:
        import google.generativeai as genai
    except Exception:
        return f"[FAKE AI OUTPUT] {prompt[:160]}..."

    api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    if not api_key:
        return f"[FAKE AI OUTPUT] {prompt[:160]}..."

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(GEMINI_MODEL)
        sys_prefix = (system + "\n\n") if system else ""
        out = model.generate_content(sys_prefix + prompt)
        return (getattr(out, "text", "") or "").strip()
    except Exception as e:
        return f"[FAKE AI OUTPUT due to error: {e}] {prompt[:160]}..."



# Public LLM wrapper
def llm(prompt: str, system: str = "") -> str:
    if PROVIDER == "gemini":
        return _call_gemini(prompt, system)
    return _call_openai(prompt, system)



# Metrics summarization
def summarize_metrics(records: List[Dict[str, Any]]) -> str:
    """
    records: list of dicts with keys at least
      - audience: str
      - ts: int/float (timestamp)
      - open_rate: float in [0,1]
      - click_rate: float in [0,1]
      - unsub_rate: float in [0,1]
    """
    by_aud: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in records:
        # minimal validation
        if not isinstance(r, dict):
            continue
        if "audience" not in r or "ts" not in r:
            continue
        # allow missing metrics; skip if not present later
        by_aud[str(r["audience"])].append(r)

    if not by_aud:
        return "No valid metrics to summarize."

    prompt_lines = [
        "Write a brief, blunt performance recap and 3 recommendations.",
        "Use one sentence per audience for the recap.",
        ""
    ]

    have_any_comparison = False
    for aud, arr in by_aud.items():
        arr = sorted(arr, key=lambda x: x.get("ts", 0))[-6:]  # last up to 6
        if len(arr) < 2:
            # not enough history to compare
            continue

        last, prev = arr[-1], arr[-2]
        try:
            o_last = float(last["open_rate"])
            o_prev = float(prev["open_rate"])
            c_last = float(last["click_rate"])
            c_prev = float(prev["click_rate"])
            u_last = float(last["unsub_rate"])
        except Exception:
            # skip if any metric missing or non-numeric
            continue

        delta_open = (o_last - o_prev) * 100.0
        delta_click = (c_last - c_prev) * 100.0

        line = (
            f"{aud}: open {o_last*100:.1f}% ({delta_open:+.1f} pp), "
            f"click {c_last*100:.1f}% ({delta_click:+.1f} pp), "
            f"unsub {u_last*100:.2f}%."
        )
        prompt_lines.append(line)
        have_any_comparison = True

    # if not have_any_comparison:
    #     return "Not enough historical data to compare segment performance."

    if not have_any_comparison:
        return "Not enough history yet. Log a second send, then I’ll compare deltas and recommend next steps."

    prompt_lines.append("")
    prompt_lines.append("Now produce exactly 3 crisp recommendations based on these deltas.")
    prompt = "\n".join(prompt_lines)

    return llm(prompt, system="You produce short, tactical B2B marketing insights with clear next steps.")
