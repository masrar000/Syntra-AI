# import os
# import json
# import time
# import re
# from typing import Dict, Any, Optional
# from slugify import slugify
# from dotenv import load_dotenv


# # environment and configuration helpers
# load_dotenv(override=True)  # ensure .env is used in Streamlit and CLI

# PROVIDER = (os.getenv("LLM_PROVIDER") or "openai").strip().lower()
# DEFAULT_OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo-0125").strip() #bought the key
# #I have free gemini key as well but for now using OpenAI because Gemini is not that good (probably free that's why)
# DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip()

# def _get_openai_client():
#     try:
#         from openai import OpenAI
#     except Exception:
#         return None
#     key = (os.getenv("OPENAI_API_KEY") or "").strip().strip('"').strip("'")
#     if not key:
#         return None
#     return OpenAI(api_key=key)

# def _get_openai_model() -> str:
#     """
#     Return the requested model if set, otherwise a safe default.
#     NOTE: Many accounts no longer have access to gpt-4/gpt-4o by default so I am using 3.5-turbo-0125 (I used before for my LLM project)
#     """
#     return DEFAULT_OPENAI_MODEL or "gpt-3.5-turbo-0125"

# def _extract_json_anywhere(text: str) -> Optional[dict]:
#     """
#     Try multiple strategies to extract a JSON object from LLM output.
#     """
#     # direct parse
#     try:
#         return json.loads(text)
#     except Exception:
#         pass

#     # fenced code block ```json ... ```
#     fence = re.search(r"```json\s*(.*?)```", text, flags=re.S | re.I)
#     if fence:
#         try:
#             return json.loads(fence.group(1).strip())
#         except Exception:
#             pass

#     # generic fenced code block
#     fence = re.search(r"```\s*(.*?)```", text, flags=re.S | re.I)
#     if fence:
#         try:
#             return json.loads(fence.group(1).strip())
#         except Exception:
#             pass

#     # best-effort: find the first balanced {...}
#     candidate = text.strip()
#     start = candidate.find("{")
#     if start != -1:
#         depth = 0
#         for i in range(start, len(candidate)):
#             ch = candidate[i]
#             if ch == "{":
#                 depth += 1
#             elif ch == "}":
#                 depth -= 1
#                 if depth == 0:
#                     blob = candidate[start : i + 1]
#                     try:
#                         return json.loads(blob)
#                     except Exception:
#                         break
#     return None

# # OpenAI & Gemini callers
# def _call_openai(prompt: str, system: str = "") -> str:
#     client = _get_openai_client()
#     if not client:
#         return f"[FAKE AI OUTPUT] {prompt[:140]}..."

#     msgs = [{"role": "system", "content": system}] if system else []
#     msgs.append({"role": "user", "content": prompt})

#     model = _get_openai_model()
#     try:
#         resp = client.chat.completions.create(
#             model=model,
#             messages=msgs,
#             temperature=0.7,
#             max_tokens=1000,
#         )
#         return (resp.choices[0].message.content or "").strip()
#     except Exception as e:
#         # graceful fallback to a deterministic stub
#         return f"[FAKE AI OUTPUT due to error: {e}] {prompt[:140]}..."

# def _call_gemini(prompt: str, system: str = "") -> str:
#     try:
#         import google.generativeai as genai
#     except Exception:
#         return f"[FAKE AI OUTPUT] {prompt[:140]}..."

#     api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
#     if not api_key:
#         return f"[FAKE AI OUTPUT] {prompt[:140]}..."

#     genai.configure(api_key=api_key)
#     model_id = DEFAULT_GEMINI_MODEL
#     try:
#         model = genai.GenerativeModel(model_id)
#         sys_prefix = (system + "\n\n") if system else ""
#         out = model.generate_content(sys_prefix + prompt)
#         return (getattr(out, "text", "") or "").strip()
#     except Exception as e:
#         return f"[FAKE AI OUTPUT due to error: {e}] {prompt[:140]}..."

# def llm(prompt: str, system: str = "") -> str:
#     if PROVIDER == "gemini":
#         return _call_gemini(prompt, system)
#     return _call_openai(prompt, system)

# # Main content generator
# def make_blog_and_newsletters(topic: str) -> Dict[str, Any]:
#     """
#     Generates:
#       - ~600-word blog
#       - Three persona-tailored newsletters (founder, creative, ops)
#         Each newsletter returns JSON:
#           { subject_main, subject_alt1, subject_alt2, preview_text, body }
#       - Title variants (as a JSON list string)
#     """
#     system = "You are a sharp B2B marketing copywriter. Be specific, practical, and persuasive. No fluff."

#     # Blog
#     blog_prompt = f"""Write a ~600 word blog post on: "{topic}".
# Target audience is a general B2B reader. Focus on automation benefits, realistic examples, and measurable outcomes.
# Use short paragraphs, no jargon. Include 3 concrete tips and a closing CTA to subscribe to a newsletter."""
#     blog = llm(blog_prompt, system)

#     # Persona newsletters
#     def persona_prompt(persona: str, focus: str) -> str:
#         return f"""From the following blog content, write a concise newsletter tailored to {persona}.
# Emphasize {focus}. 170-220 words, punchy and skimmable with exactly 3 bullets, a one-line CTA, and a P.S. with 1 data point.
# Return strict JSON with fields: subject_main, subject_alt1, subject_alt2, preview_text, body.
# Avoid extra commentary or markdown. Only return JSON."""

#     personas = {
#         "founder": "ROI and efficiency outcomes",
#         "creative": "inspiration, concept quality, and time-saving",
#         "ops": "workflow reliability, integrations, stability",
#     }

#     newsletters: Dict[str, Dict[str, str]] = {}
#     for key, focus in personas.items():
#         raw = llm(persona_prompt(key, focus) + "\n\nBLOG:\n" + blog, system)
#         parsed = _extract_json_anywhere(raw)
#         if not isinstance(parsed, dict):
#             # fallback wrapper
#             parsed = {
#                 "subject_main": f"{topic} - {key} edition",
#                 "subject_alt1": f"{topic}: quick wins for {key}s",
#                 "subject_alt2": f"{topic}: ideas you can ship today",
#                 "preview_text": "Practical takeaways from this week's piece.",
#                 "body": raw,
#             }
#         # ensuring all keys exist
#         for req in ("subject_main", "subject_alt1", "subject_alt2", "preview_text", "body"):
#             parsed.setdefault(req, "")
#         newsletters[key] = parsed  # type: ignore

#     # Title variants (as a JSON list string)
#     titles_raw = llm(
#         f"Give me 3 alternative SEO-friendly blog titles for: {topic}. Return ONLY a JSON list of strings.",
#         system,
#     )
#     # keeping raw; UI/consumers can parse or show as-is

#     slug = slugify(topic)[:60]
#     ts = int(time.time())

#     return {
#         "topic": topic,
#         "slug": slug,
#         "created_ts": ts,
#         "blog": blog,
#         "newsletters": newsletters,
#         "variants": {
#             "titles": titles_raw
#         },
#     }




import os
import json
import time
import re
from typing import Dict, Any, Optional
from slugify import slugify
from dotenv import load_dotenv

# environment and configuration helpers
load_dotenv(override=True)  # ensure .env is used in Streamlit and CLI

PROVIDER = (os.getenv("LLM_PROVIDER") or "openai").strip().lower()
DEFAULT_OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo-0125").strip()
DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip()

def _get_openai_client():
    try:
        from openai import OpenAI
    except Exception:
        return None
    key = (os.getenv("OPENAI_API_KEY") or "").strip().strip('"').strip("'")
    if not key:
        return None
    return OpenAI(api_key=key)

def _get_openai_model() -> str:
    """
    Return the requested model if set, otherwise a safe default.
    Many accounts do not have 4/4o access by default, so 3.5-turbo-0125 is used.
    """
    return DEFAULT_OPENAI_MODEL or "gpt-3.5-turbo-0125"

def _extract_json_anywhere(text: str) -> Optional[dict]:
    """
    Try multiple strategies to extract a JSON object from LLM output.
    """
    # direct parse
    try:
        return json.loads(text)
    except Exception:
        pass

    # fenced code block ```json ... ```
    fence = re.search(r"```json\s*(.*?)```", text, flags=re.S | re.I)
    if fence:
        try:
            return json.loads(fence.group(1).strip())
        except Exception:
            pass

    # generic fenced code block
    fence = re.search(r"```\s*(.*?)```", text, flags=re.S | re.I)
    if fence:
        try:
            return json.loads(fence.group(1).strip())
        except Exception:
            pass

    # best-effort: find the first balanced {...}
    candidate = text.strip()
    start = candidate.find("{")
    if start != -1:
        depth = 0
        for i in range(start, len(candidate)):
            ch = candidate[i]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    blob = candidate[start : i + 1]
                    try:
                        return json.loads(blob)
                    except Exception:
                        break
    return None

# OpenAI & Gemini callers
def _call_openai(prompt: str, system: str = "") -> str:
    client = _get_openai_client()
    if not client:
        return f"[FAKE AI OUTPUT] {prompt[:140]}..."

    msgs = [{"role": "system", "content": system}] if system else []
    msgs.append({"role": "user", "content": prompt})

    model = _get_openai_model()
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=msgs,
            temperature=0.7,
            max_tokens=1000,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        # graceful fallback to a deterministic stub
        return f"[FAKE AI OUTPUT due to error: {e}] {prompt[:140]}..."

def _call_gemini(prompt: str, system: str = "") -> str:
    try:
        import google.generativeai as genai
    except Exception:
        return f"[FAKE AI OUTPUT] {prompt[:140]}..."

    api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    if not api_key:
        return f"[FAKE AI OUTPUT] {prompt[:140]}..."

    genai.configure(api_key=api_key)
    model_id = DEFAULT_GEMINI_MODEL
    try:
        model = genai.GenerativeModel(model_id)
        sys_prefix = (system + "\n\n") if system else ""
        out = model.generate_content(sys_prefix + prompt)
        return (getattr(out, "text", "") or "").strip()
    except Exception as e:
        return f"[FAKE AI OUTPUT due to error: {e}] {prompt[:140]}..."

def llm(prompt: str, system: str = "") -> str:
    if PROVIDER == "gemini":
        return _call_gemini(prompt, system)
    return _call_openai(prompt, system)

# Main content generator
def make_blog_and_newsletters(topic: str) -> Dict[str, Any]:
    """
    Generates:
      - ~600-word blog
      - Three persona-tailored newsletters (founder, creative, ops)
        Each newsletter returns JSON:
          { subject_main, subject_alt1, subject_alt2, preview_text, body }
      - Title variants as a parsed list
    """
    system = "You are a sharp B2B marketing copywriter. Be specific, practical, and persuasive. No fluff."

    # Blog
    blog_prompt = f"""Write a ~600 word blog post on: "{topic}".
Target audience is a general B2B reader. Focus on automation benefits, realistic examples, and measurable outcomes.
Use short paragraphs, no jargon. Include 3 concrete tips and a closing CTA to subscribe to a newsletter."""
    blog = llm(blog_prompt, system)

    # Persona newsletters
    def persona_prompt(persona: str, focus: str) -> str:
        return f"""From the following blog content, write a concise newsletter tailored to {persona}.
Emphasize {focus}. 170-220 words, punchy and skimmable with exactly 3 bullets, a one-line CTA, and a P.S. with 1 data point.
Return strict JSON with fields: subject_main, subject_alt1, subject_alt2, preview_text, body.
Avoid extra commentary or markdown. Only return JSON."""

    personas = {
        "founder": "ROI and efficiency outcomes",
        "creative": "inspiration, concept quality, and time-saving",
        "ops": "workflow reliability, integrations, stability",
    }

    newsletters: Dict[str, Dict[str, str]] = {}
    for key, focus in personas.items():
        raw = llm(persona_prompt(key, focus) + "\n\nBLOG:\n" + blog, system)
        parsed = _extract_json_anywhere(raw)
        if not isinstance(parsed, dict):
            parsed = {
                "subject_main": f"{topic} - {key} edition",
                "subject_alt1": f"{topic}: quick wins for {key}s",
                "subject_alt2": f"{topic}: ideas you can ship today",
                "preview_text": "Practical takeaways from this week's piece.",
                "body": raw,
            }
        for req in ("subject_main", "subject_alt1", "subject_alt2", "preview_text", "body"):
            parsed.setdefault(req, "")
        newsletters[key] = parsed  # type: ignore

    # Title variants, parse to a list
    titles_raw = llm(
        f"Give me 3 alternative SEO-friendly blog titles for: {topic}. Return ONLY a JSON list of strings.",
        system,
    )
    try:
        titles = json.loads(titles_raw)
        if not isinstance(titles, list):
            titles = [str(titles_raw).strip()]
    except Exception:
        titles = [str(titles_raw).strip()]

    slug = slugify(topic)[:60]
    ts = int(time.time())

    return {
        "topic": topic,
        "slug": slug,
        "created_ts": ts,
        "blog": blog,
        "newsletters": newsletters,
        "variants": {
            "titles": titles
        },
    }
