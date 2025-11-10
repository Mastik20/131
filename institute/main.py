"""Console application for managing an institute."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from .course import Course
from .department import Department
from .faculty import Faculty
from .group import Group
from .institute import Institute
from .student import Student

DATA_FILE = Path("institute_data.json")


def load_institute() -> Institute:
    if DATA_FILE.exists():
        with DATA_FILE.open("r", encoding="utf-8") as fh:
            raw_data = json.load(fh)
        try:
            return Institute.from_dict(raw_data)
        except (KeyError, ValueError, TypeError) as exc:
            print(f"Failed to load institute data: {exc}. Starting fresh.")
    name = input("Enter the name of the institute: ").strip() or "My Institute"
    return Institute(name=name)


def save_institute(institute: Institute) -> None:
    with DATA_FILE.open("w", encoding="utf-8") as fh:
        json.dump(institute.to_dict(), fh, ensure_ascii=False, indent=2)
    print(f"Data saved to {DATA_FILE.resolve()}")


def get_int(prompt: str) -> int:
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("Please enter a valid integer.")


def get_float(prompt: str, *, minimum: float = 0.0, maximum: float = 100.0) -> float:
    while True:
        try:
            value = float(input(prompt))
        except ValueError:
            print("Please enter a valid number.")
            continue
        if not minimum <= value <= maximum:
            print(f"Value must be between {minimum} and {maximum}.")
            continue
        return value


def choose_course(institute: Institute) -> Course | None:
    number = get_int("Enter course number (1-6): ")
    course = institute.find_course(number)
    if course is None:
        print(f"Course {number} not found.")
    return course


def choose_faculty(course: Course) -> Faculty | None:
    name = input("Enter faculty name: ").strip()
    faculty = course.find_faculty(name.title())
    if faculty is None:
        print(f"Faculty {name} not found in course {course.number}.")
    return faculty


def choose_department(faculty: Faculty) -> Department | None:
    name = input("Enter department name: ").strip()
    department = faculty.find_department(name.title())
    if department is None:
        print(f"Department {name} not found in faculty {faculty.name}.")
    return department


def choose_group(department: Department) -> Group | None:
    name = input("Enter group name: ").strip()
    group = department.find_group(name.title())
    if group is None:
        print(f"Group {name} not found in department {department.name}.")
    return group


def add_course_flow(institute: Institute) -> None:
    name = input("Course name: ").strip() or "Unnamed Course"
    number = get_int("Course number (1-6): ")
    try:
        institute.add_course(Course(name=name, number=number))
        print("Course added.")
    except ValueError as exc:
        print(f"Failed to add course: {exc}")


def remove_course_flow(institute: Institute) -> None:
    number = get_int("Course number to remove: ")
    try:
        institute.remove_course(number)
        print("Course removed.")
    except ValueError as exc:
        print(exc)


def add_faculty_flow(institute: Institute) -> None:
    course = choose_course(institute)
    if not course:
        return
    name = input("Faculty name: ").strip()
    try:
        course.add_faculty(Faculty(name=name))
        print("Faculty added.")
    except ValueError as exc:
        print(f"Failed to add faculty: {exc}")


def remove_faculty_flow(institute: Institute) -> None:
    course = choose_course(institute)
    if not course:
        return
    name = input("Faculty name to remove: ").strip()
    try:
        course.remove_faculty(name.title())
        print("Faculty removed.")
    except ValueError as exc:
        print(exc)


def add_department_flow(institute: Institute) -> None:
    course = choose_course(institute)
    if not course:
        return
    faculty = choose_faculty(course)
    if not faculty:
        return
    name = input("Department name: ").strip()
    try:
        faculty.add_department(Department(name=name))
        print("Department added.")
    except ValueError as exc:
        print(f"Failed to add department: {exc}")


def remove_department_flow(institute: Institute) -> None:
    course = choose_course(institute)
    if not course:
        return
    faculty = choose_faculty(course)
    if not faculty:
        return
    name = input("Department name to remove: ").strip()
    try:
        faculty.remove_department(name.title())
        print("Department removed.")
    except ValueError as exc:
        print(exc)


def add_group_flow(institute: Institute) -> None:
    course = choose_course(institute)
    if not course:
        return
    faculty = choose_faculty(course)
    if not faculty:
        return
    department = choose_department(faculty)
    if not department:
        return
    name = input("Group name: ").strip()
    try:
        department.add_group(Group(name=name))
        print("Group added.")
    except ValueError as exc:
        print(f"Failed to add group: {exc}")


def remove_group_flow(institute: Institute) -> None:
    course = choose_course(institute)
    if not course:
        return
    faculty = choose_faculty(course)
    if not faculty:
        return
    department = choose_department(faculty)
    if not department:
        return
    name = input("Group name to remove: ").strip()
    try:
        department.remove_group(name.title())
        print("Group removed.")
    except ValueError as exc:
        print(exc)


def add_student_flow(institute: Institute) -> None:
    course = choose_course(institute)
    if not course:
        return
    faculty = choose_faculty(course)
    if not faculty:
        return
    department = choose_department(faculty)
    if not department:
        return
    group = choose_group(department)
    if not group:
        return

    first_name = input("Student first name: ")
    last_name = input("Student last name: ")
    student_id = input("Student ID: ")
    average_grade = get_float("Average grade (0-100): ")
    try:
        group.add_student(
            Student(
                first_name=first_name,
                last_name=last_name,
                student_id=student_id,
                average_grade=average_grade,
            )
        )
        print("Student added.")
    except ValueError as exc:
        print(f"Failed to add student: {exc}")


def remove_student_flow(institute: Institute) -> None:
    course = choose_course(institute)
    if not course:
        return
    faculty = choose_faculty(course)
    if not faculty:
        return
    department = choose_department(faculty)
    if not department:
        return
    group = choose_group(department)
    if not group:
        return
    student_id = input("Student ID to remove: ").strip()
    try:
        group.remove_student(student_id)
        print("Student removed.")
    except ValueError as exc:
        print(exc)


def show_institute_info(institute: Institute) -> None:
    print("\n=== Institute Overview ===")
    print(institute)
    print("==========================\n")


MENU_ACTIONS: dict[str, tuple[str, Callable[[Institute], None]]] = {
    "1": ("Show institute info", show_institute_info),
    "2": ("Add course", add_course_flow),
    "3": ("Remove course", remove_course_flow),
    "4": ("Add faculty to course", add_faculty_flow),
    "5": ("Remove faculty from course", remove_faculty_flow),
    "6": ("Add department to faculty", add_department_flow),
    "7": ("Remove department from faculty", remove_department_flow),
    "8": ("Add group to department", add_group_flow),
    "9": ("Remove group from department", remove_group_flow),
    "10": ("Add student to group", add_student_flow),
    "11": ("Remove student from group", remove_student_flow),
    "12": ("Save data", save_institute),
}


def main() -> None:
    institute = load_institute()
    while True:
        print("\n==== Institute Management ====")
        for key, (description, _) in MENU_ACTIONS.items():
            print(f"{key}. {description}")
        print("0. Save and exit")
        choice = input("Choose an option: ").strip()

        if choice == "0":
            save_institute(institute)
            print("Goodbye!")
            break
        action = MENU_ACTIONS.get(choice)
        if action is None:
            print("Unknown option. Please try again.")
            continue
        description, handler = action
        print(f"\n-- {description} --")
        handler(institute)


if __name__ == "__main__":
    main()
