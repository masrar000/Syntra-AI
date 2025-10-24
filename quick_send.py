# quick_send.py
import os
from dotenv import load_dotenv
import hubspot_client as hs

load_dotenv()
print(hs.single_send_marketing_email(
    email_id=os.getenv("HUBSPOT_EMAIL_TEMPLATE_ID"),
    to_addresses=["your.email@gmail.com"],
    custom_props={"persona": "founder", "blogSlug": "ai-and-automation"},
))
