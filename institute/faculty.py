"""Faculty entity containing departments."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List

from institute.department import Department
from institute.university_entity import UniversityEntity


@dataclass
class Faculty(UniversityEntity):
    """Represents a faculty within the institute."""

    _departments: List[Department] = field(default_factory=list, repr=False)

    @property
    def departments(self) -> tuple[Department, ...]:
        return tuple(self._departments)

    def add_department(self, department: Department) -> None:
        if any(existing.name == department.name for existing in self._departments):
            raise ValueError(f"Department {department.name} already exists in faculty {self.name}.")
        self._departments.append(department)

    def extend_departments(self, departments: Iterable[Department]) -> None:
        for department in departments:
            self.add_department(department)

    def remove_department(self, name: str) -> None:
        for idx, department in enumerate(self._departments):
            if department.name == name:
                del self._departments[idx]
                return
        raise ValueError(f"Department {name} not found in faculty {self.name}.")

    def find_department(self, name: str) -> Department | None:
        return next((department for department in self._departments if department.name == name), None)

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "departments": [department.to_dict() for department in self._departments],
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Faculty":
        faculty = cls(name=str(data["name"]))
        departments_data = data.get("departments", [])
        if isinstance(departments_data, list):
            for raw_department in departments_data:
                faculty.add_department(Department.from_dict(raw_department))
        return faculty

    def __str__(self) -> str:
        department_names = ", ".join(department.name for department in self._departments) or "No departments"
        return f"Faculty {self.name}: {department_names}"
