from __future__ import annotations

from typing import Any

from .base import StorageBackend


class NotionStorage(StorageBackend):
    def __init__(self, token: str, database_id: str) -> None:
        self.token = token
        self.database_id = database_id

    def save_material(self, payload: dict[str, Any]) -> str:
        return "TODO(stage2) notion save"

    def search_materials(self, query: str) -> list[dict[str, Any]]:
        return []
