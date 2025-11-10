"""Course entity containing faculties."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List

from .faculty import Faculty
from .university_entity import UniversityEntity


@dataclass
class Course(UniversityEntity):
    """Represents a course year (1-6)."""

    number: int
    _faculties: List[Faculty] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        super().__post_init__()
        if not 1 <= int(self.number) <= 6:
            raise ValueError("Course number must be between 1 and 6.")
        self.number = int(self.number)

    @property
    def faculties(self) -> tuple[Faculty, ...]:
        return tuple(self._faculties)

    def add_faculty(self, faculty: Faculty) -> None:
        if any(existing.name == faculty.name for existing in self._faculties):
            raise ValueError(f"Faculty {faculty.name} already exists in course {self.number}.")
        self._faculties.append(faculty)

    def extend_faculties(self, faculties: Iterable[Faculty]) -> None:
        for faculty in faculties:
            self.add_faculty(faculty)

    def remove_faculty(self, name: str) -> None:
        for idx, faculty in enumerate(self._faculties):
            if faculty.name == name:
                del self._faculties[idx]
                return
        raise ValueError(f"Faculty {name} not found in course {self.number}.")

    def find_faculty(self, name: str) -> Faculty | None:
        return next((faculty for faculty in self._faculties if faculty.name == name), None)

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "number": self.number,
            "faculties": [faculty.to_dict() for faculty in self._faculties],
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Course":
        course = cls(name=str(data.get("name", f"Course {data['number']}")), number=int(data["number"]))
        faculties_data = data.get("faculties", [])
        if isinstance(faculties_data, list):
            for raw_faculty in faculties_data:
                course.add_faculty(Faculty.from_dict(raw_faculty))
        return course

    def __str__(self) -> str:
        faculty_names = ", ".join(faculty.name for faculty in self._faculties) or "No faculties"
        return f"Course {self.number} ({self.name}): {faculty_names}"
