from __future__ import annotations

import json
from typing import Any

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


def create_base_resume(
    direction: str,
    bullet_ids: list[str],
    content: str,
) -> str:
    """创建一个 base 简历版本（某个方向的基础模板）。"""
    return _get_backend().create_base_resume(
        direction=direction,
        bullet_ids=bullet_ids,
        content=content,
    )


def create_resume_version(
    name: str,
    base_id: str,
    jd: dict[str, Any],
    bullet_ids: list[str],
    content: str,
) -> str:
    """基于 base 创建一个针对特定 JD 的 patch 版本，自动计算 diff。"""
    return _get_backend().create_resume_version(
        name=name,
        base_id=base_id,
        jd=jd,
        bullet_ids=bullet_ids,
        content=content,
    )


def list_resumes(direction: str | None = None) -> str:
    """列出简历版本，可按方向筛选。"""
    return json.dumps(
        _get_backend().list_resumes(direction=direction),
        ensure_ascii=False,
    )


def get_resume(resume_id: str) -> str:
    """获取完整简历内容（含 frontmatter 和正文）。"""
    return json.dumps(
        _get_backend().get_resume(resume_id),
        ensure_ascii=False,
    )
