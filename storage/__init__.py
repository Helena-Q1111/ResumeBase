"""Storage backends for resume-agent."""

from __future__ import annotations

from typing import Any

from .base import StorageBackend
from .markdown import MarkdownStorage


def create_backend(config: dict[str, Any]) -> StorageBackend:
    """Create a storage backend instance from config."""
    storage_cfg = config.get("storage", {})
    backend = storage_cfg.get("backend", "markdown")

    if backend == "markdown":
        vault_path = storage_cfg.get("vault_path", "./data")
        return MarkdownStorage(vault_path=vault_path)

    raise ValueError(f"Unknown storage backend: {backend}")
