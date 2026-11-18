import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app import models
from app.models.master_data import TimeSlot


DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]


def normalize_day(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    lowered = value.strip().lower()
    for day in DAYS:
        if lowered == day.lower() or lowered.startswith(day[:3].lower()):
            return day
    return None


def normalize_text(value: Optional[str]) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


class TimetableChangeService:
    def __init__(self, db: Session):
        self.db = db

    def preview_change(self, action: Dict[str, Any], term: str = "Fall 2025") -> Dict[str, Any]:
        action_type = action.get("type")
        params = action.get("params") or {}
        from_day = normalize_day(params.get("from_day"))
        target_days = [normalize_day(day) for day in params.get("target_days", []) if normalize_day(day)]
        target_days = [day for day in target_days if day != from_day]

        if action_type not in {"MOVE_GROUP_DAY_SESSIONS", "MOVE_TEACHER_DAY_SESSIONS"}:
            return self._empty_result("I can only move group-day or teacher-day sessions right now.", action)
        if not from_day:
            return self._empty_result("Please specify the day to move sessions from.", action)

        entries = self._find_entries(action_type, params, from_day, term)
        if not entries:
            subject = params.get("group_name") or params.get("teacher_name") or "the requested item"
            return self._empty_result(f"No timetable sessions found for {subject} on {from_day}.", action)

        occupied: Set[Tuple[str, str, str]] = set()
        moves = []
        conflicts = []

        for entry in entries:
            target_slot = self._find_target_slot(entry, from_day, target_days, occupied)
            if not target_slot:
                conflicts.append(f"No free compatible slot found for {self._entry_label(entry)} away from {from_day}.")
                continue

            occupied.update(self._reservation_keys(entry, target_slot))
            moves.append(self._move_payload(entry, target_slot))

        used_fallback_days = False
        if not moves and conflicts and target_days:
            occupied = set()
            fallback_moves = []
            fallback_conflicts = []

            for entry in entries:
                target_slot = self._find_target_slot(entry, from_day, [], occupied)
                if not target_slot:
                    fallback_conflicts.append(
                        f"No free compatible slot found for {self._entry_label(entry)} away from {from_day}."
                    )
                    continue

                occupied.update(self._reservation_keys(entry, target_slot))
                fallback_moves.append(self._move_payload(entry, target_slot))

            if fallback_moves:
                moves = fallback_moves
                conflicts = fallback_conflicts
                used_fallback_days = True

        message = f"Found {len(entries)} session(s). "
        if moves:
            if used_fallback_days:
                requested = ", ".join(target_days)
                message += f"No compatible slots were available on {requested}, so I found {len(moves)} move(s) on other days."
            else:
                message += f"I can move {len(moves)} session(s)."
        if conflicts:
            message += f" {len(conflicts)} session(s) have conflicts."

        return {
            "response": message,
            "proposal": {
                "term": term,
                "action": action,
                "moves": moves,
                "conflicts": conflicts,
            },
            "updated_config": None,
            "action": action,
        }

    def apply_change(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        term = proposal.get("term") or "Fall 2025"
        action = proposal.get("action") or {}
        fresh = self.preview_change(action, term=term)
        moves = fresh.get("proposal", {}).get("moves", [])

        requested_ids = {move.get("entry_id") for move in proposal.get("moves", [])}
        if requested_ids:
            moves = [move for move in moves if move.get("entry_id") in requested_ids]

        applied = []
        skipped = []
        for move in moves:
            entry = self.db.query(models.TimetableEntry).filter(
                models.TimetableEntry.id == UUID(move["entry_id"])
            ).first()
            slot = self.db.query(TimeSlot).filter(TimeSlot.id == UUID(move["to_time_slot_id"])).first()
            if not entry or not slot:
                skipped.append(f"Missing entry or slot for {move.get('course_code')}")
                continue

            entry.time_slot_id = slot.id
            entry.day = slot.day_of_week
            entry.time_range = self._slot_range(slot)
            applied.append(move)

        if applied:
            self.db.commit()
        else:
            self.db.rollback()

        response = f"Applied {len(applied)} timetable move(s)."
        if not applied:
            response = "No timetable moves were applied because no compatible free slot was available."

        return {
            "response": response,
            "applied": applied,
            "skipped": skipped + fresh.get("proposal", {}).get("conflicts", []),
        }

    def _empty_result(self, response: str, action: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "response": response,
            "proposal": {"term": "Fall 2025", "action": action, "moves": [], "conflicts": [response]},
            "updated_config": None,
            "action": action,
        }

    def _find_entries(
        self,
        action_type: str,
        params: Dict[str, Any],
        from_day: str,
        term: str,
    ) -> List[models.TimetableEntry]:
        query = (
            self.db.query(models.TimetableEntry)
            .options(
                joinedload(models.TimetableEntry.course),
                joinedload(models.TimetableEntry.teacher),
                joinedload(models.TimetableEntry.room),
                joinedload(models.TimetableEntry.time_slot),
            )
            .filter(
                models.TimetableEntry.term == term,
                func.lower(models.TimetableEntry.day) == from_day.lower(),
            )
        )

        if action_type == "MOVE_GROUP_DAY_SESSIONS":
            group_name = normalize_text(params.get("group_name"))
            entries = query.all()
            return [entry for entry in entries if group_name and group_name in normalize_text(entry.student_group)]

        teacher_name = normalize_text(params.get("teacher_name"))
        entries = query.all()
        return [
            entry
            for entry in entries
            if teacher_name
            and entry.teacher
            and teacher_name in normalize_text(entry.teacher.name)
        ]

    def _find_target_slot(
        self,
        entry: models.TimetableEntry,
        from_day: str,
        target_days: List[str],
        occupied: Set[Tuple[str, str, str]],
    ) -> Optional[TimeSlot]:
        source_slot = entry.time_slot
        days = target_days or [day for day in DAYS if day != from_day]
        source_duration = self._duration_minutes(source_slot)
        candidate_slots = (
            self.db.query(TimeSlot)
            .filter(
                TimeSlot.day_of_week.in_(days),
                TimeSlot.is_break == False,  # noqa: E712
            )
            .all()
        )

        sorted_slots = sorted(
            [slot for slot in candidate_slots if self._duration_minutes(slot) == source_duration],
            key=lambda slot: (DAYS.index(slot.day_of_week) if slot.day_of_week in DAYS else 99, slot.start_time),
        )

        for slot in sorted_slots:
            if self._has_reserved_conflict(entry, slot, occupied):
                continue
            if not self._has_conflict(entry, slot):
                return slot
        return None

    def _has_conflict(self, entry: models.TimetableEntry, slot: TimeSlot) -> bool:
        conflicts = (
            self.db.query(models.TimetableEntry)
            .filter(
                models.TimetableEntry.id != entry.id,
                models.TimetableEntry.term == entry.term,
                models.TimetableEntry.time_slot_id == slot.id,
            )
            .all()
        )
        for other in conflicts:
            if other.room_id == entry.room_id:
                return True
            if entry.teacher_id and other.teacher_id == entry.teacher_id:
                return True
            if other.student_group == entry.student_group:
                return True
            if entry.batch_id and other.batch_id == entry.batch_id:
                return True
        return False

    def _reservation_keys(self, entry: models.TimetableEntry, slot: TimeSlot) -> Set[Tuple[str, str, str]]:
        slot_id = str(slot.id)
        keys = {
            ("room", str(entry.room_id), slot_id),
            ("group", normalize_text(entry.student_group), slot_id),
        }
        if entry.teacher_id:
            keys.add(("teacher", str(entry.teacher_id), slot_id))
        if entry.batch_id:
            keys.add(("batch", str(entry.batch_id), slot_id))
        return keys

    def _has_reserved_conflict(
        self,
        entry: models.TimetableEntry,
        slot: TimeSlot,
        occupied: Set[Tuple[str, str, str]],
    ) -> bool:
        return any(key in occupied for key in self._reservation_keys(entry, slot))

    def _move_payload(self, entry: models.TimetableEntry, slot: TimeSlot) -> Dict[str, Any]:
        return {
            "entry_id": str(entry.id),
            "course_code": entry.course_code,
            "teacher": entry.teacher.name if entry.teacher else None,
            "student_group": entry.student_group,
            "room": entry.room_name,
            "from_day": entry.day,
            "from_time": entry.time_range,
            "to_day": slot.day_of_week,
            "to_time": self._slot_range(slot),
            "to_time_slot_id": str(slot.id),
        }

    def _entry_label(self, entry: models.TimetableEntry) -> str:
        return f"{entry.course_code} / {entry.student_group} / {entry.time_range}"

    def _slot_range(self, slot: TimeSlot) -> str:
        return f"{slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')}"

    def _duration_minutes(self, slot: TimeSlot) -> int:
        start = datetime.combine(datetime.today(), slot.start_time)
        end = datetime.combine(datetime.today(), slot.end_time)
        return int((end - start).total_seconds() // 60)
