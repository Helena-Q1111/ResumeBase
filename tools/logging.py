from __future__ import annotations

import json

from storage.base import StorageBackend

_backend: StorageBackend | None = None


def init(backend: StorageBackend) -> None:
    """Called once by server.py at startup to inject the storage backend."""
    global _backend
    _backend = backend


def _get_backend() -> StorageBackend:
    if _backend is None:
        raise RuntimeError("Storage backend not initialized. Call init() first.")
    return _backend


def get_experiences() -> str:
    """列出所有已有经历，判断 bullet 归属前调用。"""
    return json.dumps(_get_backend().get_experiences(), ensure_ascii=False)


def create_experience(
    organization: str,
    role: str,
    start: str,
    exp_type: str,
    end: str | None = None,
    direction_tags: list[str] | None = None,
    skill_tags: list[str] | None = None,
    tool_tags: list[str] | None = None,
) -> str:
    """用户有新经历时建立锚点，log_bullet 前必须先有对应 experience。"""
    return _get_backend().create_experience(
        organization=organization,
        role=role,
        start=start,
        exp_type=exp_type,
        end=end,
        direction_tags=direction_tags,
        skill_tags=skill_tags,
        tool_tags=tool_tags,
    )


def log_bullet(
    exp_id: str,
    raw: str,
    rewritten: str,
    skill_tags: list[str] | None = None,
    tool_tags: list[str] | None = None,
    category: str = "achievement",
    has_number: bool = False,
    metric_values: list[str] | None = None,
) -> str:
    """写入一条提炼好的 bullet，rewritten 由 agent 在调用前生成。"""
    return _get_backend().log_bullet(
        exp_id=exp_id,
        raw=raw,
        rewritten=rewritten,
        skill_tags=skill_tags,
        tool_tags=tool_tags,
        category=category,
        has_number=has_number,
        metric_values=metric_values,
    )
