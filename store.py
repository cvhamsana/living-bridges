import json, os, secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class DogStore:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def all(self) -> list[dict[str, Any]]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []

    def save_all(self, rows: list[dict[str, Any]]) -> None:
        temp = self.path.with_suffix(".tmp")
        temp.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
        temp.replace(self.path)

    def next_id(self) -> str:
        ids = [r.get("dog_id", "") for r in self.all()]
        used = {int(x.split("-")[-1]) for x in ids if x.startswith("LB-") and x.split("-")[-1].isdigit()}
        n = 1
        while n in used:
            n += 1
        return f"LB-{n:05d}"

    def add(self, payload: dict, embedding: list[float] | None, qr_file: str | None) -> dict:
        rows = self.all()
        stamp = now_iso()
        token = secrets.token_urlsafe(10)
        row = {
            **payload, "dog_id": self.next_id(), "created_at": stamp,
            "updated_at": stamp, "caregiver_token": token, "qr_file": qr_file,
            "embedding": embedding, "embedding_status": "available" if embedding else "not_available"
        }
        rows.append(row)
        self.save_all(rows)
        return row

    def get(self, dog_id: str) -> dict | None:
        return next((r for r in self.all() if r.get("dog_id") == dog_id), None)

    def update(self, dog_id: str, changes: dict) -> dict | None:
        rows = self.all()
        for row in rows:
            if row.get("dog_id") == dog_id:
                row.update({k:v for k,v in changes.items() if v is not None})
                row["updated_at"] = now_iso()
                self.save_all(rows)
                return row
        return None

    def public(self, row: dict) -> dict:
        # Never return raw caregiver phone number or embedding in public API.
        result = {k:v for k,v in row.items() if k not in {"embedding", "caregiver_contact"}}
        result["caregiver_contact"] = "Protected — contact via authorised coordinator"
        return result
