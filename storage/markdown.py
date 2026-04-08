from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import frontmatter

from .base import StorageBackend

# ── default body templates ──────────────────────────────────────────

EXPERIENCE_TEMPLATE = """\
## 背景

## 我的角色

## 项目结果

## 面试亮点
"""

BULLET_TEMPLATE = """\
## 原始记录
{raw}

## 提炼后
{rewritten}

## 待补充
"""

RESUME_TEMPLATE = """\
## 简历正文
"""


class MarkdownStorage(StorageBackend):
    """Store everything as Markdown files with YAML frontmatter."""

    def __init__(self, vault_path: str = "./data") -> None:
        self.vault = Path(vault_path)
        self.experiences_dir = self.vault / "experiences"
        self.materials_dir = self.vault / "materials"
        self.resumes_dir = self.vault / "resumes"

        for d in (self.experiences_dir, self.materials_dir, self.resumes_dir):
            d.mkdir(parents=True, exist_ok=True)

    # ── internal helpers ────────────────────────────────────────────

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _new_id(self, prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex[:6]}"

    # ── StorageBackend interface ────────────────────────────────────

    def load_db(self) -> dict[str, Any]:
        """Load all experiences and their bullets into a dict."""
        db: dict[str, Any] = {"experiences": {}}
        for path in self.experiences_dir.glob("*.md"):
            post = frontmatter.load(str(path))
            exp_id = post.metadata.get("id", path.stem)
            db["experiences"][exp_id] = {**post.metadata, "content": post.content}

        # attach bullets to their parent experience
        for path in self.materials_dir.glob("*.md"):
            post = frontmatter.load(str(path))
            exp_id = post.metadata.get("exp_id")
            if exp_id and exp_id in db["experiences"]:
                exp = db["experiences"][exp_id]
                exp.setdefault("bullets", {})[post.metadata.get("id", path.stem)] = {
                    **post.metadata,
                    "content": post.content,
                }
        return db

    def save_db(self, db: dict[str, Any]) -> None:
        """Not used for markdown backend — each operation writes directly."""
        pass

    def get_experiences(self) -> list[dict[str, Any]]:
        """List all experiences with summary info."""
        results: list[dict[str, Any]] = []
        for path in sorted(self.experiences_dir.glob("*.md")):
            post = frontmatter.load(str(path))
            meta = dict(post.metadata)
            # count bullets belonging to this experience
            exp_id = meta.get("id", path.stem)
            bullet_count = sum(
                1
                for bp in self.materials_dir.glob("*.md")
                if frontmatter.load(str(bp)).metadata.get("exp_id") == exp_id
            )
            meta["bullet_count"] = bullet_count
            results.append(meta)
        return results

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
        exp_id = self._new_id("exp")
        now = self._now()

        meta: dict[str, Any] = {
            "id": exp_id,
            "organization": organization,
            "role": role,
            "start": start,
            "end": end or "",
            "type": exp_type,
            "direction_tags": direction_tags or [],
            "skill_tags": skill_tags or [],
            "tool_tags": tool_tags or [],
            "created_at": now,
            "updated_at": now,
        }

        post = frontmatter.Post(EXPERIENCE_TEMPLATE, **meta)
        path = self.experiences_dir / f"{exp_id}.md"
        path.write_text(frontmatter.dumps(post), encoding="utf-8")

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
        # verify experience exists
        matching = list(self.experiences_dir.glob(f"{exp_id}.md"))
        if not matching:
            raise ValueError(f"Experience {exp_id} not found")

        bullet_id = self._new_id("bul")
        now = self._now()

        meta: dict[str, Any] = {
            "id": bullet_id,
            "exp_id": exp_id,
            "category": category,
            "skill_tags": skill_tags or [],
            "tool_tags": tool_tags or [],
            "has_number": has_number,
            "metric_values": metric_values or [],
            "created_at": now,
        }

        body = BULLET_TEMPLATE.format(raw=raw, rewritten=rewritten)
        post = frontmatter.Post(body, **meta)
        path = self.materials_dir / f"{bullet_id}.md"
        path.write_text(frontmatter.dumps(post), encoding="utf-8")

        return bullet_id
