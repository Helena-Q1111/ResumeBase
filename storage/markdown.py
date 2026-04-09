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
{content}
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

    def _find_by_id(self, directory: Path, target_id: str) -> frontmatter.Post:
        """在指定目录下按 frontmatter id 查找，找不到抛异常。"""
        for path in directory.glob("*.md"):
            post = frontmatter.load(str(path))
            if post.metadata.get("id") == target_id:
                return post
        raise ValueError(f"ID {target_id} not found in {directory.name}")

    # ── StorageBackend interface ────────────────────────────────────

    def get_experiences(self) -> list[dict[str, Any]]:
        """List all experiences with summary info."""
        results: list[dict[str, Any]] = []
        for path in sorted(self.experiences_dir.glob("*.md")):
            post = frontmatter.load(str(path))
            meta = dict(post.metadata)
            # count bullets belonging to this experience
            exp_id = meta.get("id")
            project_name = meta.get("project_name")
            direction = meta.get("direction")

            if project_name and direction:
                bullet_dir = self.materials_dir / f"{project_name}-{direction}"
                bullet_count = sum(1 for _ in bullet_dir.glob("*.md")) if bullet_dir.exists() else 0
            else:
                bullet_count = 0

            meta["bullet_count"] = bullet_count
            results.append(meta)
        return results

    def create_experience(
        self,
        project_name: str,
        direction: str,
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

        # filename: {project_name}-{direction}.md
        file_prefix = f"{project_name}-{direction}"

        meta: dict[str, Any] = {
            "id": exp_id,
            "project_name": project_name,
            "direction": direction,
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
        path = self.experiences_dir / f"{file_prefix}.md"
        path.write_text(frontmatter.dumps(post), encoding="utf-8")

        return exp_id

    def log_bullet(
        self,
        exp_id: str,
        bullet_name: str,
        raw: str,
        rewritten: str,
        skill_tags: list[str] | None = None,
        tool_tags: list[str] | None = None,
        category: str = "achievement",
        has_number: bool = False,
        metric_values: list[str] | None = None,
    ) -> str:
        exp_post = self._find_by_id(self.experiences_dir, exp_id)

        project_name = exp_post.metadata.get("project_name")
        direction = exp_post.metadata.get("direction")
        file_prefix = f"{project_name}-{direction}"

        # create bullet folder if not exists
        bullet_dir = self.materials_dir / file_prefix
        bullet_dir.mkdir(parents=True, exist_ok=True)

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
        path = bullet_dir / f"{bullet_name}.md"
        path.write_text(frontmatter.dumps(post), encoding="utf-8")

        return bullet_id

    # ── resume version management ──────────────────────────────────

    def create_base_resume(
        self,
        direction: str,
        bullet_ids: list[str],
        content: str,
    ) -> str:
        # find project_name from first bullet
        project_name = None
        if bullet_ids:
            first_bullet_id = bullet_ids[0]
            for exp_path in self.experiences_dir.glob("*.md"):
                exp_post = frontmatter.load(str(exp_path))
                exp_id = exp_post.metadata.get("id")
                if exp_id:
                    bullet_dir = self.materials_dir / f"{exp_post.metadata.get('project_name')}-{exp_post.metadata.get('direction')}"
                    if bullet_dir.exists():
                        for bullet_path in bullet_dir.glob("*.md"):
                            bullet_post = frontmatter.load(str(bullet_path))
                            if bullet_post.metadata.get("id") == first_bullet_id:
                                project_name = exp_post.metadata.get("project_name")
                                break
                if project_name:
                    break

        if not project_name:
            raise ValueError("Cannot determine project_name from bullet_ids")

        resume_id = self._new_id("res")
        now = self._now()
        file_name = f"{project_name}-{direction}-base"

        meta: dict[str, Any] = {
            "id": resume_id,
            "name": file_name,
            "direction": direction,
            "project_name": project_name,
            "is_base": True,
            "base_id": None,
            "jd": None,
            "bullet_ids": bullet_ids,
            "diff_from_base": None,
            "export_path": "",
            "created_at": now,
        }

        body = RESUME_TEMPLATE.format(content=content)
        post = frontmatter.Post(body, **meta)
        path = self.resumes_dir / f"{file_name}.md"
        path.write_text(frontmatter.dumps(post), encoding="utf-8")

        return resume_id

    def create_resume_version(
        self,
        name: str,
        base_id: str,
        jd: dict[str, Any],
        bullet_ids: list[str],
        content: str,
    ) -> str:
        base_post = self._find_by_id(self.resumes_dir, base_id)

        base_bullet_ids = set(base_post.metadata.get("bullet_ids", []))
        current_ids = set(bullet_ids)

        diff: list[dict[str, str]] = []
        for bid in current_ids - base_bullet_ids:
            diff.append({"action": "add", "bullet_id": bid})
        for bid in base_bullet_ids - current_ids:
            diff.append({"action": "remove", "bullet_id": bid})

        resume_id = self._new_id("res")
        now = self._now()
        project_name = base_post.metadata.get("project_name", "")
        direction = base_post.metadata.get("direction", "")
        file_name = f"{project_name}-{direction}-{name}"

        meta: dict[str, Any] = {
            "id": resume_id,
            "name": name,
            "project_name": project_name,
            "direction": direction,
            "is_base": False,
            "base_id": base_id,
            "jd": jd,
            "bullet_ids": bullet_ids,
            "diff_from_base": diff or None,
            "export_path": "",
            "created_at": now,
        }

        body = RESUME_TEMPLATE.format(content=content)
        post = frontmatter.Post(body, **meta)
        path = self.resumes_dir / f"{file_name}.md"
        path.write_text(frontmatter.dumps(post), encoding="utf-8")

        return resume_id

    def list_resumes(self, direction: str | None = None) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for path in sorted(self.resumes_dir.glob("*.md")):
            post = frontmatter.load(str(path))
            meta = dict(post.metadata)
            if direction and meta.get("direction") != direction:
                continue
            results.append({
                "id": meta.get("id"),
                "name": meta.get("name"),
                "direction": meta.get("direction"),
                "is_base": meta.get("is_base"),
                "created_at": meta.get("created_at"),
            })
        return results

    def get_resume(self, resume_id: str) -> dict[str, Any]:
        post = self._find_by_id(self.resumes_dir, resume_id)
        return {**post.metadata, "content": post.content}
