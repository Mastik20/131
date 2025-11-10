"""Group entity containing students."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List

from .student import Student
from .university_entity import UniversityEntity


@dataclass
class Group(UniversityEntity):
    """Represents a student group."""

    _students: List[Student] = field(default_factory=list, repr=False)

    @property
    def students(self) -> tuple[Student, ...]:
        """Return an immutable view of the students."""
        return tuple(self._students)

    def add_student(self, student: Student) -> None:
        """Add a student if the ID is unique."""
        if any(existing.student_id == student.student_id for existing in self._students):
            raise ValueError(f"Student with ID {student.student_id} already in group {self.name}.")
        self._students.append(student)

    def extend_students(self, students: Iterable[Student]) -> None:
        for student in students:
            self.add_student(student)

    def remove_student(self, student_id: str) -> None:
        """Remove a student by ID."""
        for idx, student in enumerate(self._students):
            if student.student_id == student_id:
                del self._students[idx]
                return
        raise ValueError(f"Student with ID {student_id} not found in group {self.name}.")

    def find_student(self, student_id: str) -> Student | None:
        return next((student for student in self._students if student.student_id == student_id), None)

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "students": [student.to_dict() for student in self._students],
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Group":
        group = cls(name=str(data["name"]))
        students_data = data.get("students", [])
        if isinstance(students_data, list):
            for raw_student in students_data:
                group.add_student(Student.from_dict(raw_student))
        return group

    def __str__(self) -> str:
        student_info = ", ".join(student.student_id for student in self._students) or "No students"
        return f"Group {self.name}: {student_info}"
