from __future__ import annotations

from typing import Any

from .base import StorageBackend


class ObsidianStorage(StorageBackend):
    def __init__(self, vault_path: str) -> None:
        self.vault_path = vault_path

    def save_material(self, payload: dict[str, Any]) -> str:
        return "TODO(stage2) obsidian save"

    def search_materials(self, query: str) -> list[dict[str, Any]]:
        return []
