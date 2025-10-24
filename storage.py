import os, json, time, pathlib
from typing import Dict, Any

ROOT = "data"
CONTENT_DIR = f"{ROOT}/content"
PERF_DIR = f"{ROOT}/perf"
CRM_DIR = f"{ROOT}/crm"
for p in (CONTENT_DIR, PERF_DIR, CRM_DIR):
    os.makedirs(p, exist_ok=True)

def save_content(payload: Dict[str, Any]) -> str:
    date = time.strftime("%Y%m%d")
    path = f"{CONTENT_DIR}/{date}-{payload['slug']}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path

def list_content_files():
    return sorted([str(p) for p in pathlib.Path(CONTENT_DIR).glob("*.json")])

def read_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def append_metrics(record: Dict[str, Any]):
    with open(f"{PERF_DIR}/metrics.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def dump_summary(summary: str):
    with open(f"{PERF_DIR}/summary.json", "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "ts": int(time.time())}, f, ensure_ascii=False, indent=2)

def append_send_log(record: Dict[str, Any]):
    with open(f"{CRM_DIR}/send_log.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def overwrite_content(path: str, payload: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
