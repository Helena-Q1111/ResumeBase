from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class StorageBackend(ABC):
    """Abstract storage backend interface."""

    @abstractmethod
    def save_material(self, payload: dict[str, Any]) -> str:
        raise NotImplementedError

    @abstractmethod
    def search_materials(self, query: str) -> list[dict[str, Any]]:
        raise NotImplementedError
