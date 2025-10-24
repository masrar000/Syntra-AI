import os, json, time, datetime
import streamlit as st
from dotenv import load_dotenv
import google_docs_client as gdocs
import content_engine as ce
import hubspot_client as hs
import storage as store
import simulate_metrics as sim
import llm_summary as lsum

#setting up app
st.set_page_config(page_title="AI Marketing Pipeline", page_icon="🧠", layout="wide")
load_dotenv()
hs.init_crm()

st.title("AI Marketing Pipeline — Blog → Newsletters → Send → Performance")

#sidebars
with st.sidebar:
    st.header("Settings")
    st.markdown("**LLM Provider:** " + os.getenv("LLM_PROVIDER", "openai"))
    st.markdown("**HubSpot token set:** " + ("✅" if hs.hubspot_available() else "❌"))
    st.markdown("**Email send via API:** " + ("✅" if hs.can_send() else "❌ simulate"))
    st.divider()
    st.subheader("Helpful Docs")
    st.markdown("[Marketing Email API](https://developers.hubspot.com/docs/api-reference/marketing-marketing-emails-v3-v3/guide)")
    st.markdown("[Single-send API](https://developers.hubspot.com/docs/api-reference/marketing-single-send-v4/guide)")
    st.markdown("[Lists (Segments) API](https://developers.hubspot.com/docs/api-reference/crm-lists-v3/guide)")

tab1, tab2, tab3, tab4 = st.tabs(["1) Generate Content", "2) Distribute", "3) Performance", "4) Data Browser"])

#Tab 1: Generate 
with tab1:
    st.subheader("Blog ideation and persona newsletters")
    topic = st.text_input("Topic (weekly blog)", "Automation that actually ships: small stacks, big ROI")

    if st.button("Generate blog + 3 newsletters", key="gen_blog_newsletters"):
        payload = ce.make_blog_and_newsletters(topic)

        #Creating the Google Doc and storing the URL
        try:
            doc_url = gdocs.create_blog_doc(payload.get("topic",""), payload.get("blog",""))
            payload["doc_url"] = doc_url
            st.success(f"Google Doc created ✔  \n{doc_url}")
            st.markdown(f"[Open the doc]({doc_url})")
        except Exception as e:
            payload["doc_url"] = ""
            st.warning(f"Couldn’t create Google Doc automatically: {e}")

        path = store.save_content(payload)
        st.success(f"Generated and saved: {path}")
        st.text_area("Blog (editable before sending)", payload["blog"], height=260, key="blog_edit")
        st.write("Newsletters JSON:")
        st.json(payload["newsletters"])


#Tab 2: Distribute
with tab2:
    st.subheader("Distribute via HubSpot (or simulate)")

    # Get files and normalize for Windows/Linux
    raw_files = store.list_content_files()
    def norm(p: str) -> str:
        return p.replace("\\", "/")

    # Keep only real content JSON files (exclude our index helper, if any)
    files = [p for p in raw_files
             if norm(p).endswith(".json")
             and "google_docs_index" not in norm(p)
             and "/content/" in norm(p)]

    if not files:
        st.info("No content yet. Generate in tab 1.")
    else:
        choice = st.selectbox("Pick content file", files, index=len(files) - 1, key="content_choice")
        data = store.read_json(choice)

        # --- One-time: auto-create a Google Doc if missing and save back to the same file ---
        if not data.get("doc_url"):
            try:
                url = gdocs.create_blog_doc(
                    title=data.get("topic", "Untitled"),
                    body=data.get("blog", "")
                )
                data["doc_url"] = url
                with open(choice, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                st.success("✅ Created Google Doc and saved its URL in the content file.")
            except Exception as e:
                st.warning(f"⚠️ Couldn’t create Doc automatically: {e}")

        # --- Show blog meta & preview ---
        st.write(f"**Blog:** {data.get('topic','')}  |  slug: `{data.get('slug','')}`")
        if data.get("doc_url"):
            st.markdown(f"**Doc URL:** {data['doc_url']}  \n[Open the doc]({data['doc_url']})")
        else:
            st.info("This content file has no `doc_url`. The CTA will fall back to BLOG_BASE_URL (if set).")

        st.text_area("Blog body", data.get("blog", ""), height=180, key="blog_readonly")

        # Persona setup and validation
        persona_map = {"Founders": "founder", "Creatives": "creative", "Operations": "ops"}
        missing = [k for k in ["founder", "creative", "ops"] if k not in (data.get("newsletters") or {})]
        if missing:
            st.error(f"Content file missing persona newsletters for: {', '.join(missing)}")

        st.markdown("**Audience and sending**")
        cols = st.columns(3)

        send_date = st.date_input("Send date", value=datetime.date.today(), key="send_date")
        to_placeholder = st.text_input(
            "Optional test recipients (comma-separated emails). Leave blank to target persona lists",
            key="test_recipients"
        )

        # Helper to build props (prefers Google Doc URL; otherwise BLOG_BASE_URL + slug)
        def build_props(keyp: str) -> dict:
            nl = (data.get("newsletters") or {}).get(keyp, {})
            slug = data.get("slug", "")
            doc_url = data.get("doc_url") or ""
            base = os.getenv("BLOG_BASE_URL", "").rstrip("/")

            # CTA priority: explicit NL CTA → doc_url → BLOG_BASE_URL/slug → BLOG_BASE_URL → docs home
            fallback = f"{base}/{slug}" if base and slug else base
            cta_url = nl.get("cta_url") or doc_url or fallback or "https://docs.google.com"

            return {
                "persona": keyp,
                "blog_slug": slug,
                "blog_title": data.get("topic", ""),
                "blog_excerpt": nl.get("excerpt") or data.get("blog", "")[:200],
                "nl_subject": nl.get("subject") or f"{data.get('topic','')} — for {keyp}",
                "nl_preheader": nl.get("preheader") or "This week’s top automation insight",
                "nl_headline": nl.get("headline") or data.get("topic", ""),
                "nl_body": nl.get("body") or "Quick take: focus on fewer, more useful automations.",
                "cta_text": nl.get("cta_text") or "Read the full post",
                "cta_url": cta_url,
            }

        # Per-persona send buttons
        for label, keyp in persona_map.items():
            with cols[["Founders", "Creatives", "Operations"].index(label)]:
                st.write(f"**{label}**")
                st.json((data.get("newsletters") or {}).get(keyp, {}))

                if st.button(f"Send {label}", key=f"send_{keyp}"):
                    # Ensure dynamic list (ok if simulated)
                    seg = hs.ensure_persona_list(keyp)
                    if seg.get("status") == "error":
                        st.error(f"List error: {seg}")

                    # Resolve recipients
                    addresses = [e.strip() for e in to_placeholder.split(",") if e.strip()] or [f"{keyp}@example.com"]

                    # Make sure contacts exist & are tagged by persona
                    for addr in addresses:
                        hs.upsert_contact(addr, {"persona": keyp})

                    # Send with full custom properties (for HubL tokens)
                    props = build_props(keyp)
                    result = hs.single_send_marketing_email(
                        email_id=os.getenv("HUBSPOT_EMAIL_TEMPLATE_ID", "REPLACE_WITH_TEMPLATE_ID"),
                        to_addresses=addresses,
                        custom_props=props,
                    )

                    # Log locally
                    record = {
                        "ts": int(time.time()),
                        "send_date": str(send_date),
                        "audience": keyp,
                        "blog_title": data.get("topic", ""),
                        "newsletter_id": f"{data.get('slug','')}-{keyp}",
                        "hubspot_result": result,
                    }
                    store.append_send_log(record)
                    st.success(f"Sent (or simulated). Result: {result}")

        # Send ALL personas (same recipients typed above, per-persona props)
        if st.button("Send all personas", key="send_all_personas"):
            for _, keyp in persona_map.items():
                addresses = [e.strip() for e in to_placeholder.split(",") if e.strip()] or [f"{keyp}@example.com"]
                for addr in addresses:
                    hs.upsert_contact(addr, {"persona": keyp})

                props = build_props(keyp)
                result = hs.single_send_marketing_email(
                    email_id=os.getenv("HUBSPOT_EMAIL_TEMPLATE_ID", "REPLACE_WITH_TEMPLATE_ID"),
                    to_addresses=addresses,
                    custom_props=props,
                )

                record = {
                    "ts": int(time.time()),
                    "send_date": str(send_date),
                    "audience": keyp,
                    "blog_title": data.get("topic", ""),
                    "newsletter_id": f"{data.get('slug','')}-{keyp}",
                    "hubspot_result": result,
                }
                store.append_send_log(record)

            st.success("Sent (or simulated) to all personas.")

        # Save blog edits back to the SAME file
        if st.button("Save blog edits", key="save_blog_edits"):
            data["blog"] = st.session_state.get("blog_readonly", data.get("blog", ""))
            with open(choice, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            st.success(f"Saved changes back to {choice}.")

        if not data.get("newsletters"):
            st.error("This content file has no newsletters.")




# ---------- Tab 3: Performance ----------
with tab3:
    st.subheader("Performance logging and AI summary")
    st.caption("If you can't pull real metrics yet, simulate them to build the flow.")

    cols = st.columns(3)
    for idx, aud in enumerate(["founder", "creative", "ops"]):
        with cols[idx]:
            if st.button(f"Simulate 1 send for {aud}", key=f"sim_{aud}"):
                m = sim.simulate_performance(aud)
                store.append_metrics(m)
                st.success(f"Logged: {m}")

    import pandas as pd
    perf_path = "data/perf/metrics.jsonl"
    if os.path.exists(perf_path):
        rows = [json.loads(line) for line in open(perf_path, "r", encoding="utf-8").read().splitlines() if line.strip()]
        if rows:
            df = pd.DataFrame(rows)
            st.write("Recent metrics")
            st.dataframe(df.tail(30), use_container_width=True, hide_index=True)
            st.line_chart(df.pivot_table(index="ts", columns="audience", values="open_rate").fillna(method="ffill"))
            st.line_chart(df.pivot_table(index="ts", columns="audience", values="click_rate").fillna(method="ffill"))
            st.line_chart(df.pivot_table(index="ts", columns="audience", values="unsub_rate").fillna(method="ffill"))
            if st.button("Write AI performance summary", key="write_ai_summary"):
                text = lsum.summarize_metrics(rows)
                store.dump_summary(text)
                st.success("Summary updated.")
        else:
            st.info("No metrics logged yet.")
    else:
        st.info("No metrics file found. Simulate above.")

    summ_path = "data/perf/summary.json"
    if os.path.exists(summ_path):
        st.write("Latest AI summary")
        st.json(json.load(open(summ_path)))

# ---------- Tab 4: Data Browser ----------
with tab4:
    st.subheader("Browse raw data")
    st.code("data/content/*  data/perf/*.jsonl  data/crm/send_log.jsonl")
    import glob
    st.write("Content files")
    for p in glob.glob("data/content/*.json"):
        st.write("-", p)
    if os.path.exists("data/crm/send_log.jsonl"):
        st.write("Send log (tail)")
        tail = "\n".join(open("data/crm/send_log.jsonl", "r", encoding="utf-8").read().splitlines()[-20:])
        st.code(tail or "(empty)")
