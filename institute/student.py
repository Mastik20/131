"""Student entity."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Student:
    """Represents a student with personal data and academic performance."""

    first_name: str
    last_name: str
    student_id: str
    average_grade: float = field(default=0.0)

    def __post_init__(self) -> None:
        self.first_name = self._validate_name(self.first_name, "first name")
        self.last_name = self._validate_name(self.last_name, "last name")
        self.student_id = self.student_id.strip()
        self.average_grade = self._validate_grade(self.average_grade)

    @staticmethod
    def _validate_name(value: str, field_name: str) -> str:
        if not value or not value.strip():
            raise ValueError(f"Student {field_name} cannot be empty.")
        return value.strip().title()

    @staticmethod
    def _validate_grade(value: float) -> float:
        if not 0 <= float(value) <= 100:
            raise ValueError("Average grade must be between 0 and 100.")
        return float(value)

    def update_grade(self, new_grade: float) -> None:
        """Set a new average grade."""
        self.average_grade = self._validate_grade(new_grade)

    def to_dict(self) -> dict[str, object]:
        """Serialize the student to a dictionary."""
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "student_id": self.student_id,
            "average_grade": self.average_grade,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Student":
        """Create a Student instance from serialized data."""
        return cls(
            first_name=str(data["first_name"]),
            last_name=str(data["last_name"]),
            student_id=str(data["student_id"]),
            average_grade=float(data.get("average_grade", 0.0)),
        )

    def __str__(self) -> str:
        return (
            f"{self.first_name} {self.last_name} (ID: {self.student_id}, "
            f"Average Grade: {self.average_grade:.2f})"
        )
