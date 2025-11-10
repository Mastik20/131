"""Base class for named university entities."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class UniversityEntity:
    """Base class that stores the name of an entity."""

    name: str

    def __post_init__(self) -> None:
        self.name = self._validate_name(self.name)

    @staticmethod
    def _validate_name(value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Name cannot be empty.")
        return value.strip().title()

    def rename(self, new_name: str) -> None:
        """Change the name of the entity."""
        self.name = self._validate_name(new_name)

    def __str__(self) -> str:  # pragma: no cover - trivial dataclass output
        return self.name
