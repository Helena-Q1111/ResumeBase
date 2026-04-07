from __future__ import annotations

from typing import Any

from .base import StorageBackend


class LocalJSONStorage(StorageBackend):
    def __init__(self, base_path: str = "./data") -> None:
        self.base_path = base_path

    def save_material(self, payload: dict[str, Any]) -> str:
        return "TODO(stage2) local save"

    def search_materials(self, query: str) -> list[dict[str, Any]]:
        return []
