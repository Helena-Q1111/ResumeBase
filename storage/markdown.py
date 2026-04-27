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

LANGUAGE_LABELS = {
    "en": "English",
    "zh": "中文",
    "ja": "日本語",
}


def _format_rewritten(rewritten: dict[str, str]) -> str:
    """Render multilingual rewritten dict into a readable Markdown block."""
    if len(rewritten) == 1:
        return next(iter(rewritten.values()))
    lines = []
    for lang, text in rewritten.items():
        label = LANGUAGE_LABELS.get(lang, lang.upper())
        lines.append(f"**{label}:** {text}")
    return "\n\n".join(lines)

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

    def _find_path_by_id(self, directory: Path, target_id: str) -> tuple[Path, frontmatter.Post]:
        """Locate a markdown file by frontmatter id; return (path, post)."""
        for path in directory.glob("*.md"):
            post = frontmatter.load(str(path))
            if post.metadata.get("id") == target_id:
                return path, post
        raise ValueError(f"ID {target_id} not found in {directory.name}")

    def _find_bullet_path_by_id(self, bullet_id: str) -> tuple[Path, frontmatter.Post]:
        """Locate a bullet by id across all material subdirectories."""
        for path in self.materials_dir.glob("*/*.md"):
            post = frontmatter.load(str(path))
            if post.metadata.get("id") == bullet_id:
                return path, post
        raise ValueError(f"Bullet ID {bullet_id} not found")

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
        rewritten: dict[str, str],
        skill_tags: list[str] | None = None,
        tool_tags: list[str] | None = None,
        category: str = "achievement",
        has_number: bool = False,
        metric_values: list[str] | None = None,
    ) -> str:
        if not rewritten:
            raise ValueError("rewritten must contain at least one language")

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
            "languages": list(rewritten.keys()),
            "raw": raw,
            "rewritten": dict(rewritten),
            "skill_tags": skill_tags or [],
            "tool_tags": tool_tags or [],
            "has_number": has_number,
            "metric_values": metric_values or [],
            "created_at": now,
        }

        body = BULLET_TEMPLATE.format(raw=raw, rewritten=_format_rewritten(rewritten))
        post = frontmatter.Post(body, **meta)
        path = bullet_dir / f"{bullet_name}.md"
        path.write_text(frontmatter.dumps(post), encoding="utf-8")

        return bullet_id

    def list_bullets(self, exp_id: str) -> list[dict[str, Any]]:
        """List all bullets under an experience."""
        exp_post = self._find_by_id(self.experiences_dir, exp_id)
        project_name = exp_post.metadata.get("project_name")
        direction = exp_post.metadata.get("direction")
        bullet_dir = self.materials_dir / f"{project_name}-{direction}"

        results: list[dict[str, Any]] = []
        if not bullet_dir.exists():
            return results

        for path in sorted(bullet_dir.glob("*.md")):
            post = frontmatter.load(str(path))
            meta = dict(post.metadata)
            results.append({
                "id": meta.get("id"),
                "bullet_name": path.stem,
                "category": meta.get("category"),
                "languages": meta.get("languages", []),
                "rewritten": meta.get("rewritten", {}),
                "skill_tags": meta.get("skill_tags", []),
                "tool_tags": meta.get("tool_tags", []),
                "has_number": meta.get("has_number", False),
                "metric_values": meta.get("metric_values", []),
                "content": post.content,
            })
        return results

    # ── partial updates ────────────────────────────────────────────

    def update_experience(
        self,
        exp_id: str,
        organization: str | None = None,
        role: str | None = None,
        start: str | None = None,
        end: str | None = None,
        exp_type: str | None = None,
        direction_tags: list[str] | None = None,
        skill_tags: list[str] | None = None,
        tool_tags: list[str] | None = None,
    ) -> dict[str, Any]:
        path, post = self._find_path_by_id(self.experiences_dir, exp_id)
        meta = dict(post.metadata)

        if organization is not None:
            meta["organization"] = organization
        if role is not None:
            meta["role"] = role
        if start is not None:
            meta["start"] = start
        if end is not None:
            meta["end"] = end
        if exp_type is not None:
            meta["type"] = exp_type
        if direction_tags is not None:
            meta["direction_tags"] = direction_tags
        if skill_tags is not None:
            meta["skill_tags"] = skill_tags
        if tool_tags is not None:
            meta["tool_tags"] = tool_tags

        meta["updated_at"] = self._now()

        new_post = frontmatter.Post(post.content, **meta)
        path.write_text(frontmatter.dumps(new_post), encoding="utf-8")
        return meta

    def update_bullet(
        self,
        bullet_id: str,
        bullet_name: str | None = None,
        raw: str | None = None,
        rewritten: dict[str, str] | None = None,
        skill_tags: list[str] | None = None,
        tool_tags: list[str] | None = None,
        category: str | None = None,
        has_number: bool | None = None,
        metric_values: list[str] | None = None,
    ) -> dict[str, Any]:
        if rewritten is not None and not rewritten:
            raise ValueError("rewritten must contain at least one language")

        path, post = self._find_bullet_path_by_id(bullet_id)
        meta = dict(post.metadata)

        if raw is not None:
            meta["raw"] = raw
        if rewritten is not None:
            meta["rewritten"] = dict(rewritten)
            meta["languages"] = list(rewritten.keys())
        if skill_tags is not None:
            meta["skill_tags"] = skill_tags
        if tool_tags is not None:
            meta["tool_tags"] = tool_tags
        if category is not None:
            meta["category"] = category
        if has_number is not None:
            meta["has_number"] = has_number
        if metric_values is not None:
            meta["metric_values"] = metric_values

        meta["updated_at"] = self._now()

        # Regenerate body if raw or rewritten changed (keeps body in sync with meta)
        if raw is not None or rewritten is not None:
            body = BULLET_TEMPLATE.format(
                raw=meta.get("raw", ""),
                rewritten=_format_rewritten(meta.get("rewritten", {})),
            )
        else:
            body = post.content

        new_post = frontmatter.Post(body, **meta)

        # Handle filename rename
        if bullet_name is not None and bullet_name != path.stem:
            new_path = path.parent / f"{bullet_name}.md"
            new_path.write_text(frontmatter.dumps(new_post), encoding="utf-8")
            path.unlink()
            path = new_path
        else:
            path.write_text(frontmatter.dumps(new_post), encoding="utf-8")

        meta["bullet_name"] = path.stem
        return meta

    # ── resume version management ──────────────────────────────────

    def create_base_resume(
        self,
        direction: str,
        bullet_ids: list[str],
        content: str,
        language: str | None = None,
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
        suffix = f"-{language}" if language else ""
        file_name = f"{project_name}-{direction}-base{suffix}"

        meta: dict[str, Any] = {
            "id": resume_id,
            "name": file_name,
            "direction": direction,
            "project_name": project_name,
            "language": language,
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
        language: str | None = None,
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
        # 默认沿用 base 的语言；显式传入 language 则覆盖
        effective_lang = language if language is not None else base_post.metadata.get("language")
        suffix = f"-{effective_lang}" if effective_lang else ""
        file_name = f"{project_name}-{direction}-{name}{suffix}"

        meta: dict[str, Any] = {
            "id": resume_id,
            "name": name,
            "project_name": project_name,
            "direction": direction,
            "language": effective_lang,
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
                "language": meta.get("language"),
                "is_base": meta.get("is_base"),
                "created_at": meta.get("created_at"),
            })
        return results

    def get_resume(self, resume_id: str) -> dict[str, Any]:
        post = self._find_by_id(self.resumes_dir, resume_id)
        return {**post.metadata, "content": post.content}
