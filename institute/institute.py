"""Institute aggregate root."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List

from institute.course import Course
from institute.university_entity import UniversityEntity


@dataclass
class Institute(UniversityEntity):
    """Represents the entire institute."""

    _courses: List[Course] = field(default_factory=list, repr=False)

    @property
    def courses(self) -> tuple[Course, ...]:
        return tuple(self._courses)

    def add_course(self, course: Course) -> None:
        if any(existing.number == course.number for existing in self._courses):
            raise ValueError(f"Course number {course.number} already exists in the institute.")
        self._courses.append(course)

    def extend_courses(self, courses: Iterable[Course]) -> None:
        for course in courses:
            self.add_course(course)

    def remove_course(self, number: int) -> None:
        for idx, course in enumerate(self._courses):
            if course.number == number:
                del self._courses[idx]
                return
        raise ValueError(f"Course number {number} not found in the institute.")

    def find_course(self, number: int) -> Course | None:
        return next((course for course in self._courses if course.number == number), None)

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "courses": [course.to_dict() for course in self._courses],
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Institute":
        institute = cls(name=str(data["name"]))
        courses_data = data.get("courses", [])
        if isinstance(courses_data, list):
            for raw_course in courses_data:
                institute.add_course(Course.from_dict(raw_course))
        return institute

    def __str__(self) -> str:
        if not self._courses:
            return f"Institute {self.name}: no courses registered"
        course_descriptions = "\n".join(str(course) for course in self._courses)
        return f"Institute {self.name} with courses:\n{course_descriptions}"
