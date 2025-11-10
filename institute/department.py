"""Department entity containing groups."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List

from .group import Group
from .university_entity import UniversityEntity


@dataclass
class Department(UniversityEntity):
    """Represents a university department."""

    _groups: List[Group] = field(default_factory=list, repr=False)

    @property
    def groups(self) -> tuple[Group, ...]:
        return tuple(self._groups)

    def add_group(self, group: Group) -> None:
        if any(existing.name == group.name for existing in self._groups):
            raise ValueError(f"Group {group.name} already exists in department {self.name}.")
        self._groups.append(group)

    def extend_groups(self, groups: Iterable[Group]) -> None:
        for group in groups:
            self.add_group(group)

    def remove_group(self, name: str) -> None:
        for idx, group in enumerate(self._groups):
            if group.name == name:
                del self._groups[idx]
                return
        raise ValueError(f"Group {name} not found in department {self.name}.")

    def find_group(self, name: str) -> Group | None:
        return next((group for group in self._groups if group.name == name), None)

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "groups": [group.to_dict() for group in self._groups],
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Department":
        department = cls(name=str(data["name"]))
        groups_data = data.get("groups", [])
        if isinstance(groups_data, list):
            for raw_group in groups_data:
                department.add_group(Group.from_dict(raw_group))
        return department

    def __str__(self) -> str:
        group_names = ", ".join(group.name for group in self._groups) or "No groups"
        return f"Department {self.name}: {group_names}"
