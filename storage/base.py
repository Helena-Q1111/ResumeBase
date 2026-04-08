from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class StorageBackend(ABC):
    """Abstract storage backend interface."""

    @abstractmethod
    def load_db(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def save_db(self, db: dict[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_experiences(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    # ── resume version management ──────────────────────────────────

    @abstractmethod
    def create_base_resume(
        self,
        direction: str,
        bullet_ids: list[str],
        content: str,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def create_resume_version(
        self,
        name: str,
        base_id: str,
        jd: dict[str, Any],
        bullet_ids: list[str],
        content: str,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def list_resumes(self, direction: str | None = None) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def get_resume(self, resume_id: str) -> dict[str, Any]:
        raise NotImplementedError
