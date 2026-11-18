from io import BytesIO
import hashlib
import math
import re
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from openpyxl import load_workbook
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models
from app.api import deps
from app.models.course import CourseType
from app.models.master_data import GlobalBreak, TeacherConstraint

router = APIRouter()

COURSE_COLUMNS = [
    {"col": 3, "kind": CourseType.THEORY, "year": "FY", "hint_col": None},
    {"col": 4, "kind": CourseType.LAB, "year": "FY", "hint_col": None},
    {"col": 6, "kind": CourseType.THEORY, "year": "SY", "hint_col": 9},
    {"col": 7, "kind": CourseType.LAB, "year": "SY", "hint_col": 9},
    {"col": 8, "kind": CourseType.TUTORIAL, "year": "SY", "hint_col": 9},
    {"col": 11, "kind": CourseType.THEORY, "year": "TY", "hint_col": 14},
    {"col": 12, "kind": CourseType.LAB, "year": "TY", "hint_col": 14},
    {"col": 13, "kind": CourseType.TUTORIAL, "year": "TY", "hint_col": 14},
    {"col": 16, "kind": CourseType.THEORY, "year": "BTECH", "hint_col": None},
    {"col": 17, "kind": CourseType.TUTORIAL, "year": "BTECH", "hint_col": None},
]

YEAR_LEVELS = {"FY": 1, "SY": 2, "TY": 3, "BTECH": 4}


def _clean_text(value: Any) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\r", "\n").replace('"', "")
    text = re.sub(r"\s+", " ", text.replace("\n", " ")).strip(" |")
    return text.strip()


def _lines(value: Any) -> List[str]:
    if value is None:
        return []
    return [
        _clean_text(part)
        for part in str(value).replace("\r", "\n").split("\n")
        if _clean_text(part)
    ]


def _slug(value: str, max_len: int) -> str:
    slug = re.sub(r"[^A-Z0-9]+", "", value.upper())
    return (slug or "X")[:max_len]


def _teacher_code(name: str) -> str:
    words = [w for w in re.findall(r"[A-Za-z0-9]+", name) if w.lower() not in {"prof", "dr"}]
    if not words:
        return "TCH"
    return "".join(word[0] for word in words[:3]).upper()


def _email_for_name(name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", ".", name.lower()).strip(".")
    base = re.sub(r"\.{2,}", ".", base) or "faculty"
    return f"{base}@example.com"


def _extract_subject(value: Any) -> Optional[str]:
    candidates = _lines(value)
    for line in candidates:
        upper = line.upper()
        if re.search(r"\b\d+\s*HR\b", upper):
            continue
        if re.fullmatch(r"\(?\s*\d+\s*B?\s*\*?\s*\d*\s*\)?\s*-?", upper):
            continue
        if re.match(r"^(FY|SY|TY|BTECH)\b", upper):
            continue
        if upper.startswith(("TH-", "LAB-", "TUT-")):
            continue
        subject = re.sub(r"\([^)]*\)", "", line).strip(" -/")
        if subject:
            return subject[:100]

    if candidates:
        fallback = re.sub(r"\([^)]*\)", "", candidates[0]).strip(" -/")
        return fallback[:100] if fallback else None
    return None


def _extract_divisions(value: Any, year: str, hint: Any = None) -> List[str]:
    text = f"{_clean_text(value)} {_clean_text(hint)}".upper()
    text = text.replace("_", "-")
    divisions: List[str] = []

    def add(prefix: str, suffix: Optional[str] = None) -> None:
        suffix = _clean_text(suffix).upper().replace("_", "-") if suffix else ""
        suffix = re.sub(r"[^A-Z0-9]+", "", suffix)
        name = prefix if not suffix else f"{prefix}-{suffix}"
        if name not in divisions:
            divisions.append(name)

    for prefix in ("FY", "SY", "TY"):
        pattern = rf"\b{prefix}\s*[- ]?\s*([A-Z0-9]+(?:\s*[,/]\s*[A-Z0-9]+)*)?"
        for match in re.finditer(pattern, text):
            raw_suffix = match.group(1)
            if not raw_suffix:
                add(prefix)
                continue
            raw_suffix = re.split(r"[-(]", raw_suffix)[0]
            for part in re.split(r"[,/]", raw_suffix):
                if part.strip():
                    add(prefix, part)

    if "BTECH" in text:
        add("BTECH")

    if not divisions:
        if year == "BTECH":
            add("BTECH")
        elif year in {"FY", "SY", "TY"}:
            if year == "SY" and "SEDA" in text:
                add("SY", "SEDA")
            else:
                add(year)

    return divisions


def _batch_count(value: Any, kind: CourseType) -> int:
    if kind == CourseType.THEORY:
        return 0

    text = _clean_text(value).upper()
    match = re.search(r"(\d+)\s*B\s*\*\s*\d+", text)
    if match:
        return max(1, min(int(match.group(1)), 6))

    match = re.search(r"(\d+)\s*\*\s*\d+", text)
    if match:
        return max(1, min(int(match.group(1)), 6))

    return 1


def _weekly_sessions(value: Any, kind: CourseType, division_count: int) -> int:
    text = _clean_text(value).upper()

    match = re.search(r"\d+\s*B?\s*\*\s*(\d+)", text)
    if kind != CourseType.THEORY and match:
        return max(1, int(match.group(1)))

    if kind == CourseType.THEORY:
        match = re.search(r"\((\d+)\)", text)
        if match:
            return max(1, int(match.group(1)))

    hr_matches = [int(v) for v in re.findall(r"(\d+)\s*HR", text)]
    if hr_matches:
        hours = hr_matches[-1]
        if kind == CourseType.THEORY and division_count > 1:
            return max(1, math.ceil(hours / division_count))
        return max(1, hours)

    if kind == CourseType.LAB:
        return 2
    return 1


def _find_teacher(db: Session, name: str) -> Optional[models.Teacher]:
    return (
        db.query(models.Teacher)
        .filter(func.lower(models.Teacher.name) == name.lower())
        .first()
    )


def _find_group(db: Session, division: str) -> Optional[models.StudentGroup]:
    normalized = division.lower()
    groups = db.query(models.StudentGroup).all()
    for group in groups:
        group_name = group.name.lower()
        if group_name == normalized or group_name.endswith(f"-{normalized}"):
            return group
    return None


def _ensure_teacher(db: Session, name: str, load: Optional[float], summary: Dict[str, int]) -> models.Teacher:
    teacher = _find_teacher(db, name)
    max_hours = max(1, int(round(load))) if load else 40
    if teacher:
        if teacher.max_weekly_hours != max_hours:
            teacher.max_weekly_hours = max_hours
            summary["teachers_updated"] += 1
        return teacher

    email = _email_for_name(name)
    existing_email = db.query(models.Teacher).filter(func.lower(models.Teacher.email) == email.lower()).first()
    if existing_email:
        digest = hashlib.sha1(name.encode("utf-8")).hexdigest()[:6]
        email = f"{email.split('@')[0]}.{digest}@example.com"

    teacher = models.Teacher(name=name, email=email, max_weekly_hours=max_hours)
    db.add(teacher)
    db.flush()
    summary["teachers_created"] += 1
    return teacher


def _ensure_group(db: Session, division: str, year: str, summary: Dict[str, int]) -> models.StudentGroup:
    group = _find_group(db, division)
    if group:
        return group

    group = models.StudentGroup(name=division, size=60, year_level=YEAR_LEVELS.get(year, 1))
    db.add(group)
    db.flush()
    summary["groups_created"] += 1
    return group


def _ensure_batch(db: Session, group: models.StudentGroup, batch_name: str, summary: Dict[str, int]) -> models.Batch:
    for batch in group.batches:
        if batch.name.lower() == batch_name.lower():
            return batch

    size = max(1, (group.size or 60) // 3)
    batch = models.Batch(name=batch_name.lower(), size=size, student_group_id=group.id)
    db.add(batch)
    db.flush()
    summary["batches_created"] += 1
    return batch


def _course_code(subject: str, division: str, kind: CourseType, batch_name: Optional[str], teacher_name: str) -> str:
    type_code = {"THEORY": "T", "LAB": "L", "TUTORIAL": "U"}[kind.value]
    batch_part = _slug(batch_name or "", 2)
    digest = hashlib.sha1(
        f"{subject}|{division}|{kind.value}|{batch_name or ''}|{teacher_name}".encode("utf-8")
    ).hexdigest()[:4].upper()
    return f"{_slug(subject, 5)}-{_slug(division, 5)}-{type_code}{batch_part}-{digest}"[:20]


def _upsert_course(
    db: Session,
    *,
    subject: str,
    division: str,
    kind: CourseType,
    sessions: int,
    teacher: models.Teacher,
    group: models.StudentGroup,
    batch: Optional[models.Batch],
    summary: Dict[str, int],
) -> None:
    code = _course_code(subject, division, kind, batch.name if batch else None, teacher.name)
    course = db.query(models.Course).filter(models.Course.code == code).first()
    if course:
        course.name = subject
        course.course_type = kind
        course.weekly_sessions = sessions
        course.teacher_id = teacher.id
        course.student_group_id = group.id
        course.batch_id = batch.id if batch else None
        summary["courses_updated"] += 1
        return

    course = models.Course(
        code=code,
        name=subject,
        course_type=kind,
        weekly_sessions=sessions,
        teacher_id=teacher.id,
        student_group_id=group.id,
        batch_id=batch.id if batch else None,
    )
    db.add(course)
    db.flush()
    summary["courses_created"] += 1


@router.post("/load-distribution", response_model=Dict[str, int])
async def import_load_distribution(
    *,
    db: Session = Depends(deps.get_db),
    file: UploadFile = File(...),
    current_user=Depends(deps.get_current_active_superuser),
) -> Dict[str, int]:
    if not file.filename.lower().endswith((".xlsx", ".xlsm")):
        raise HTTPException(status_code=400, detail="Please upload an .xlsx load distribution file.")

    content = await file.read()
    try:
        workbook = load_workbook(BytesIO(content), data_only=True)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not read workbook: {exc}") from exc

    worksheet = workbook.active
    if "faculty" not in _clean_text(worksheet.cell(1, 1).value).lower():
        raise HTTPException(status_code=400, detail="Unsupported workbook format: first column must be Faculty Name.")

    summary = {
        "teachers_created": 0,
        "teachers_updated": 0,
        "groups_created": 0,
        "batches_created": 0,
        "courses_created": 0,
        "courses_updated": 0,
        "rows_processed": 0,
    }

    current_teacher_name: Optional[str] = None
    current_teacher: Optional[models.Teacher] = None
    current_load: Optional[float] = None

    try:
        for row_idx in range(3, worksheet.max_row + 1):
            raw_name = _clean_text(worksheet.cell(row_idx, 1).value)
            if raw_name:
                current_teacher_name = raw_name
                load_value = worksheet.cell(row_idx, 2).value
                current_load = float(load_value) if isinstance(load_value, (int, float)) else None
                current_teacher = _ensure_teacher(db, current_teacher_name, current_load, summary)

            if not current_teacher or not current_teacher_name:
                continue

            row_had_course = False
            for column in COURSE_COLUMNS:
                cell_value = worksheet.cell(row_idx, column["col"]).value
                if not _clean_text(cell_value):
                    continue

                subject = _extract_subject(cell_value)
                if not subject:
                    continue

                hint_value = worksheet.cell(row_idx, column["hint_col"]).value if column["hint_col"] else None
                divisions = _extract_divisions(cell_value, column["year"], hint_value)
                if not divisions:
                    continue

                sessions = _weekly_sessions(cell_value, column["kind"], len(divisions))
                batches = _batch_count(cell_value, column["kind"])

                for division in divisions:
                    group = _ensure_group(db, division, column["year"], summary)
                    if column["kind"] == CourseType.THEORY:
                        _upsert_course(
                            db,
                            subject=subject,
                            division=division,
                            kind=column["kind"],
                            sessions=sessions,
                            teacher=current_teacher,
                            group=group,
                            batch=None,
                            summary=summary,
                        )
                    else:
                        for batch_index in range(1, batches + 1):
                            batch = _ensure_batch(db, group, f"b{batch_index}", summary)
                            _upsert_course(
                                db,
                                subject=subject,
                                division=division,
                                kind=column["kind"],
                                sessions=sessions,
                                teacher=current_teacher,
                                group=group,
                                batch=batch,
                                summary=summary,
                            )
                    row_had_course = True

            if row_had_course:
                summary["rows_processed"] += 1

        db.commit()
        return summary
    except Exception:
        db.rollback()
        raise


@router.delete("/master-data", response_model=Dict[str, int])
def reset_master_data(
    *,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_active_superuser),
) -> Dict[str, int]:
    summary = {
        "timetable_entries_deleted": db.query(models.TimetableEntry).count(),
        "courses_deleted": db.query(models.Course).count(),
        "batches_deleted": db.query(models.Batch).count(),
        "groups_deleted": db.query(models.StudentGroup).count(),
        "teachers_deleted": db.query(models.Teacher).count(),
        "teacher_constraints_deleted": db.query(TeacherConstraint).count(),
        "breaks_deleted": db.query(GlobalBreak).count(),
    }

    try:
        db.query(models.TimetableEntry).delete(synchronize_session=False)
        db.query(models.Course).delete(synchronize_session=False)
        db.query(models.Batch).delete(synchronize_session=False)
        db.query(models.StudentGroup).delete(synchronize_session=False)
        db.query(TeacherConstraint).delete(synchronize_session=False)
        db.query(models.Teacher).delete(synchronize_session=False)
        db.query(GlobalBreak).delete(synchronize_session=False)
        db.commit()
        return summary
    except Exception:
        db.rollback()
        raise
