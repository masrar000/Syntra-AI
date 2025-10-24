# # google_docs_client.py
# # Creates/updates a Google Doc and makes it public, returning a shareable URL.

# from __future__ import annotations
# import os, json, pathlib, re, time
# from typing import Optional

# from googleapiclient.discovery import build
# from googleapiclient.errors import HttpError
# from google.oauth2.credentials import Credentials
# from google_auth_oauthlib.flow import InstalledAppFlow
# from google.auth.transport.requests import Request

# # Scopes: Docs (create/write) + Drive (set public permission)
# SCOPES = [
#     "https://www.googleapis.com/auth/documents",
#     "https://www.googleapis.com/auth/drive"
# ]

# TOKEN_PATH = "token.json"
# CREDS_PATH = "credentials.json"
# INDEX_PATH = "data/content/google_docs_index.json"   # slug -> docId mapping

# def _slugify(text: str) -> str:
#     text = text.lower().strip()
#     text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
#     return text or f"blog-{int(time.time())}"

# def _load_index() -> dict:
#     if os.path.exists(INDEX_PATH):
#         try:
#             return json.load(open(INDEX_PATH, "r", encoding="utf-8"))
#         except Exception:
#             return {}
#     return {}

# def _save_index(idx: dict) -> None:
#     pathlib.Path(os.path.dirname(INDEX_PATH) or ".").mkdir(parents=True, exist_ok=True)
#     with open(INDEX_PATH, "w", encoding="utf-8") as f:
#         json.dump(idx, f, ensure_ascii=False, indent=2)

# def _get_creds() -> Credentials:
#     creds = None
#     if os.path.exists(TOKEN_PATH):
#         creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request())
#         else:
#             flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
#             creds = flow.run_local_server(port=0)
#         with open(TOKEN_PATH, "w", encoding="utf-8") as f:
#             f.write(creds.to_json())
#     return creds

# def _clear_doc(doc_service, document_id: str):
#     """Remove all content except the last trailing newline."""
#     doc = doc_service.documents().get(documentId=document_id).execute()
#     end_index = doc.get("body", {}).get("content", [])[-1]["endIndex"]
#     requests = [{"deleteContentRange": {"range": {"startIndex": 1, "endIndex": end_index-1}}}]
#     doc_service.documents().batchUpdate(documentId=document_id, body={"requests": requests}).execute()

# def _write_doc(doc_service, document_id: str, title: str, body_text: str):
#     requests = [
#         {"insertText": {"location": {"index": 1}, "text": f"{title}\n\n"}},
#         {"updateParagraphStyle": {
#             "range": {"startIndex": 1, "endIndex": 1 + len(title) + 1},
#             "paragraphStyle": {"namedStyleType": "TITLE"},
#             "fields": "namedStyleType"
#         }},
#         {"insertText": {"location": {"index": 1 + len(title) + 2}, "text": body_text}}
#     ]
#     doc_service.documents().batchUpdate(documentId=document_id, body={"requests": requests}).execute()

# def _make_public(drive_service, file_id: str):
#     # Make anyone with the link a reader
#     drive_service.permissions().create(
#         fileId=file_id,
#         body={"type": "anyone", "role": "reader"},
#         fields="id"
#     ).execute()

# def create_or_update_public_doc(title: str, body_text: str, *, slug: Optional[str] = None) -> str:
#     """
#     Creates (or updates) a Google Doc for this slug and returns the shareable URL.
#     Reuses the same Doc when the same slug is sent again.
#     """
#     slug = slug or _slugify(title)
#     creds = _get_creds()
#     docs = build("docs", "v1", credentials=creds)
#     drive = build("drive", "v3", credentials=creds)

#     index = _load_index()
#     doc_id = index.get(slug)

#     try:
#         if doc_id:
#             # Update existing
#             _clear_doc(docs, doc_id)
#         else:
#             # Create new
#             doc = docs.documents().create(body={"title": title}).execute()
#             doc_id = doc.get("documentId")
#             index[slug] = doc_id
#             _save_index(index)

#         _write_doc(docs, doc_id, title, body_text)
#         _make_public(drive, doc_id)

#         return f"https://docs.google.com/document/d/{doc_id}/edit?usp=sharing"

#     except HttpError as e:
#         raise RuntimeError(f"Google Docs/Drive error: {e}")

# # Convenience function used by app.py
# def publish_blog_to_google_doc(title: str, body_text: str, slug: Optional[str] = None) -> str:
#     return create_or_update_public_doc(title, body_text, slug=slug)

# if __name__ == "__main__":
#     # Quick auth test — runs the OAuth flow and creates a sample doc
#     url = publish_blog_to_google_doc("Auth test OK", "If you can see this, OAuth is working.")
#     print("Doc URL:", url)







# google_docs_client.py
from __future__ import annotations
import os, json, time
from typing import Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive",
]

TOKEN_PATH = "token.json"
CREDS_PATH = "credentials.json"

def _get_creds():
    creds: Optional[Credentials] = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
    return creds

def create_blog_doc(title: str, body: str, *, make_public: bool = True) -> str:
    """Create a Google Doc for the blog and return its webViewLink."""
    creds = _get_creds()
    docs = build("docs", "v1", credentials=creds)
    drive = build("drive", "v3", credentials=creds)

    doc = docs.documents().create(body={"title": title or "Untitled"}).execute()
    doc_id = doc["documentId"]

    requests = [
        {"insertText": {"location": {"index": 1},
                        "text": f"{title}\n\n{body or ''}"}}
    ]
    docs.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()

    if make_public:
        try:
            drive.permissions().create(
                fileId=doc_id,
                body={"type": "anyone", "role": "reader"},
                fields="id",
            ).execute()
        except HttpError:
            pass

    file_meta = drive.files().get(fileId=doc_id, fields="webViewLink").execute()
    return file_meta.get("webViewLink")
