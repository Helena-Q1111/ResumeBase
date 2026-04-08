from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from .base import StorageBackend


def now_iso() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class LocalJSONStorage(StorageBackend):
    def __init__(self, db_path: str = "C:\\Users\\CLoudie\\Desktop\\ResumeBase\\data\\db.json") -> None:
        self.db_path = Path(db_path)

    def load_db(self) -> dict[str, Any]:
        if not self.db_path.exists():
            return {"version": "1", "experiences": {}}

        with self.db_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            raise ValueError("db.json must be a JSON object")

        if "version" not in data:
            data["version"] = "1"
        if "experiences" not in data or not isinstance(data["experiences"], dict):
            data["experiences"] = {}

        return data

    def save_db(self, db: dict[str, Any]) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self.db_path.open("w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=2)

    def get_experiences(self) -> list[dict[str, Any]]:
        db = self.load_db()
        experiences = db.get("experiences", {})
        summaries: list[dict[str, Any]] = []

        for exp_id, exp in experiences.items():
            if not isinstance(exp, dict):
                continue
            bullets = exp.get("bullets", {})
            bullet_count = len(bullets) if isinstance(bullets, dict) else 0
            summaries.append(
                {
                    "id": exp_id,
                    "type": exp.get("type"),
                    "organization": exp.get("organization"),
                    "role": exp.get("role"),
                    "start": exp.get("start"),
                    "end": exp.get("end"),
                    "tags": exp.get("tags", {"direction": [], "skill": [], "tool": []}),
                    "bullet_count": bullet_count,
                }
            )

        return summaries

    def create_experience(
        self,
        organization: str,
        role: str,
        start: str,
        exp_type: str,
        end: str | None = None,
        direction_tags: list[str] | None = None,
        skill_tags: list[str] | None = None,
        tool_tags: list[str] | None = None,
    ) -> str:
        db = self.load_db()
        exp_id = f"exp_{uuid4().hex[:6]}"

        db.setdefault("experiences", {})[exp_id] = {
            "id": exp_id,
            "type": exp_type,
            "organization": organization,
            "role": role,
            "start": start,
            "end": end,
            "tags": {
                "direction": list(direction_tags or []),
                "skill": list(skill_tags or []),
                "tool": list(tool_tags or []),
            },
            "bullets": {},
            "created_at": now_iso(),
        }

        self.save_db(db)
        return exp_id

    def log_bullet(
        self,
        exp_id: str,
        raw: str,
        rewritten: str,
        skill_tags: list[str] | None = None,
        tool_tags: list[str] | None = None,
        category: str = "achievement",
        has_number: bool = False,
        metric_values: list[str] | None = None,
    ) -> str:
        db = self.load_db()
        experiences = db.get("experiences", {})

        if exp_id not in experiences:
            raise ValueError(f"Experience not found: {exp_id}")

        exp = experiences[exp_id]
        bullets = exp.setdefault("bullets", {})
        bul_id = f"bul_{uuid4().hex[:6]}"

        bullets[bul_id] = {
            "id": bul_id,
            "raw": raw,
            "rewritten": rewritten,
            "tags": {
                "skill": list(skill_tags or []),
                "tool": list(tool_tags or []),
            },
            "category": category,
            "metrics": {
                "has_number": has_number,
                "values": list(metric_values or []),
            },
            "created_at": now_iso(),
            "source": "chat",
        }

        self.save_db(db)
        return bul_id
