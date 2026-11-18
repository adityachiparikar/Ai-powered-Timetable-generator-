from app.services.llm.ollama_client import OllamaClient
from typing import Dict, Any
from difflib import SequenceMatcher
import re

class NLPConstraintService:
    def __init__(self):
        self.ollama = OllamaClient()

    def _local_chat_fallback(self, message: str, reason: str = "") -> Dict[str, Any]:
        lower_msg = message.lower()
        updates: Dict[str, Any] = {}
        notes = []

        load_match = re.search(r"(?:max(?:imum)?\s*(?:daily\s*)?(?:load|hours?)|load)\D+(\d+)", lower_msg)
        if load_match:
            load = max(1, min(int(load_match.group(1)), 12))
            updates["max_daily_load"] = load
            notes.append(f"max daily load to {load}")

        if "gap" in lower_msg:
            if any(word in lower_msg for word in ("disable", "off", "stop", "no ")):
                updates["minimize_gaps"] = False
                notes.append("gap minimization off")
            elif any(word in lower_msg for word in ("enable", "on", "minimize", "reduce")):
                updates["minimize_gaps"] = True
                notes.append("gap minimization on")

        if "consecutive lab" in lower_msg or "continuous lab" in lower_msg:
            if any(word in lower_msg for word in ("disable", "off", "stop", "no ")):
                updates["consecutive_labs"] = False
                notes.append("consecutive labs off")
            elif any(word in lower_msg for word in ("enable", "on", "allow", "yes")):
                updates["consecutive_labs"] = True
                notes.append("consecutive labs on")

        if "parallel lab" in lower_msg:
            if any(word in lower_msg for word in ("disable", "off", "stop", "no ")):
                updates["parallel_labs"] = False
                notes.append("parallel labs off")
            elif any(word in lower_msg for word in ("enable", "on", "allow", "yes")):
                updates["parallel_labs"] = True
                notes.append("parallel labs on")

        prefix = f"{reason} " if reason else ""
        if updates:
            return {
                "response": f"{prefix}Updated {', '.join(notes)}.",
                "updated_config": updates,
                "action": None,
            }

        if any(word in lower_msg for word in ("remove", "move", "shift", "session", "class")):
            return {
                "response": (
                    f"{prefix}For moving or removing a specific class, update the master data or constraints, "
                    "then regenerate the timetable. I can directly update soft preferences like max load, gaps, "
                    "consecutive labs, and parallel labs."
                ),
                "updated_config": None,
                "action": None,
            }

        return {
            "response": (
                f"{prefix}I can still handle basic constraint commands locally. "
                "Try: set max load to 5, enable gap minimization, disable parallel labs, or enable consecutive labs."
            ),
            "updated_config": None,
            "action": None,
        }

    def parse_timetable_action(self, message: str, db=None) -> Dict[str, Any]:
        local_action = self._parse_timetable_action_locally(message)
        if local_action:
            return local_action

        lower_msg = message.lower()
        if self._is_contextual_move_followup(message):
            return {}

        if not any(word in lower_msg for word in ("move", "remove", "shift", "session", "class", "lecture", "lab")):
            return {}

        return self._parse_timetable_action_with_ollama(message, db=db)

    def _is_vague_conflict_followup(self, message: str) -> bool:
        lower_msg = message.lower().strip()
        return bool(
            re.search(r"\b(fix|solve|resolve|clear)\b", lower_msg)
            and any(word in lower_msg for word in ("them", "it", "conflict", "conflicts", "issue", "issues"))
        )

    def _is_contextual_move_followup(self, message: str) -> bool:
        lower_msg = message.lower().strip()
        has_context_words = bool(re.search(r"\b(instead|other\s+day|another\s+day|shift\s+it|move\s+it)\b", lower_msg))
        has_pronoun = bool(re.search(r"\b(it|them)\b", lower_msg))
        has_explicit_subject = bool(
            re.search(r"\b(FY|SY|TY|BTECH)\s*[- ]?\s*([A-Z0-9]+)?\b", message, flags=re.IGNORECASE)
            or re.search(r"\b(teacher|faculty|prof(?:essor)?)\b", lower_msg)
        )
        return has_context_words and has_pronoun and not has_explicit_subject

    def _parse_timetable_action_with_ollama(self, message: str, db=None) -> Dict[str, Any]:
        knowledge = ""
        if db:
            try:
                from app.models import StudentGroup, Teacher

                teacher_names = [row.name for row in db.query(Teacher.name).limit(40).all()]
                group_names = [row.name for row in db.query(StudentGroup.name).limit(40).all()]
                knowledge = f"Known teachers: {teacher_names}\nKnown student groups: {group_names}"
            except Exception:
                knowledge = ""

        prompt = f"""
Return JSON only. Convert the user timetable edit request into one action.

Supported action types:
- MOVE_GROUP_DAY_SESSIONS: move all timetable entries for a student group away from one day.
- MOVE_TEACHER_DAY_SESSIONS: move all timetable entries for a teacher away from one day.

Schema:
{{
  "type": "MOVE_GROUP_DAY_SESSIONS" | "MOVE_TEACHER_DAY_SESSIONS" | null,
  "params": {{
    "group_name": string | null,
    "teacher_name": string | null,
    "from_day": "Monday" | "Tuesday" | "Wednesday" | "Thursday" | "Friday" | "Saturday" | null,
    "target_days": array of day names
  }}
}}

Use target_days only when the user names destination days. If they say other days, use [].
{knowledge}
User request: {message}
"""
        parsed = self.ollama.generate_json(prompt)
        if not parsed or not parsed.get("type"):
            return {}

        action_type = parsed.get("type")
        if action_type not in {"MOVE_GROUP_DAY_SESSIONS", "MOVE_TEACHER_DAY_SESSIONS"}:
            return {}

        params = parsed.get("params") or {}
        return {
            "type": action_type,
            "params": {
                "group_name": params.get("group_name"),
                "teacher_name": params.get("teacher_name"),
                "from_day": params.get("from_day"),
                "target_days": params.get("target_days") or [],
            },
        }

    def _parse_timetable_action_locally(self, message: str) -> Dict[str, Any]:
        lower_msg = message.lower()
        if not any(word in lower_msg for word in ("move", "remove", "shift")):
            return {}
        if not any(word in lower_msg for word in ("session", "class", "lecture", "lab")):
            return {}

        normalized_message = self._normalize_day_words(message)
        day_pattern = r"\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Mon|Tue|Wed|Thu|Fri|Sat)\b"
        days = self._extract_days(message)
        if not days:
            return {}

        from_day = days[0]
        target_days = days[1:]

        group_match = re.search(r"\b(FY|SY|TY|BTECH)\s*[- ]?\s*([A-Z0-9]+)?\b", normalized_message, flags=re.IGNORECASE)
        if group_match:
            group_name = group_match.group(1).upper()
            if group_match.group(2):
                group_name = f"{group_name} {group_match.group(2).upper()}"
            return {
                "type": "MOVE_GROUP_DAY_SESSIONS",
                "params": {
                    "group_name": group_name,
                    "teacher_name": None,
                    "from_day": from_day,
                    "target_days": target_days,
                },
            }

        teacher_name = ""
        teacher_match = re.search(
            rf"(?:class(?:e?s)?|sessions?|lectures?|labs?)\s+of\s+(.+?)\s+(?:from|on)\s+{day_pattern}",
            normalized_message,
            flags=re.IGNORECASE,
        )
        if teacher_match:
            teacher_name = teacher_match.group(1)
        else:
            teacher_match = re.search(
                rf"(?:faculty|teacher|prof(?:essor)?)\s+(.+?)\s+(?:from|on)\s+{day_pattern}",
                normalized_message,
                flags=re.IGNORECASE,
            )
            if teacher_match:
                teacher_name = teacher_match.group(1)

        teacher_name = re.sub(r"\b(faculty|teacher|professor)\b", "", teacher_name, flags=re.IGNORECASE)
        teacher_name = re.sub(r"\s+", " ", teacher_name).strip(" .,-")
        if teacher_name:
            return {
                "type": "MOVE_TEACHER_DAY_SESSIONS",
                "params": {
                    "group_name": None,
                    "teacher_name": teacher_name,
                    "from_day": from_day,
                    "target_days": target_days,
                },
            }

        return {}

    def _canonical_day(self, value: str) -> str | None:
        token = re.sub(r"[^a-z]", "", value.lower())
        aliases = {
            "mon": "Monday",
            "monday": "Monday",
            "tue": "Tuesday",
            "tues": "Tuesday",
            "tuesday": "Tuesday",
            "wed": "Wednesday",
            "weds": "Wednesday",
            "wednesday": "Wednesday",
            "wednsday": "Wednesday",
            "wensday": "Wednesday",
            "thurs": "Thursday",
            "thur": "Thursday",
            "thu": "Thursday",
            "thursday": "Thursday",
            "fri": "Friday",
            "friday": "Friday",
            "sat": "Saturday",
            "saturday": "Saturday",
        }
        if token in aliases:
            return aliases[token]

        if len(token) < 5:
            return None

        best_day = None
        best_score = 0.0
        for day in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"):
            score = SequenceMatcher(None, token, day.lower()).ratio()
            if score > best_score:
                best_score = score
                best_day = day

        return best_day if best_score >= 0.78 else None

    def _extract_days(self, message: str) -> list[str]:
        days: list[str] = []
        for token in re.findall(r"\b[A-Za-z]+\b", message):
            day = self._canonical_day(token)
            if day and (not days or days[-1] != day):
                days.append(day)
        return days

    def _normalize_day_words(self, message: str) -> str:
        def replace(match: re.Match[str]) -> str:
            value = match.group(0)
            return self._canonical_day(value) or value

        return re.sub(r"\b[A-Za-z]+\b", replace, message)

    def parse_constraint(self, text: str) -> Dict[str, Any]:
        """
        Parses natural language (e.g. "Prof Smith generally avoids Mondays") 
        into structured constraint data.
        """
        prompt = f"""
        Return JSON only. Extract the constraint from the following text.
        Key entities: Teacher Name, Day, Time Range, Room Type.
        
        Text: "{text}"
        
        JSON Structure:
        {{
            "teacher": "name or null",
            "day": "Monday/Tuesday/etc or null",
            "time_start": "HH:MM or null",
            "time_end": "HH:MM or null",
            "type": "AVOID/PREFER/REQUIRE"
        }}
        """

        parsed = self.ollama.generate_json(prompt)
        if not parsed:
            return {"error": "Ollama is not available or did not return valid JSON."}
        return parsed

    def _process_chat_with_ollama(
        self,
        message: str,
        current_config: Dict[str, Any],
        db=None,
    ) -> Dict[str, Any]:
        knowledge = ""
        if db:
            try:
                from app.models import Teacher, Room, StudentGroup

                t_names = [t.name for t in db.query(Teacher.name).limit(40).all()]
                r_names = [r.name for r in db.query(Room.name).limit(40).all()]
                g_names = [g.name for g in db.query(StudentGroup.name).limit(40).all()]
                knowledge = f"""
Known entities:
- Teachers: {', '.join(t_names)}
- Rooms: {', '.join(r_names)}
- Student Groups: {', '.join(g_names)}
"""
            except Exception:
                knowledge = ""

        prompt = f"""
Return JSON only. You are the timetable assistant.

Use this schema:
{{
  "response": "short user-facing explanation",
  "updated_config": {{
    "max_daily_load": integer or null,
    "minimize_gaps": boolean or null,
    "consecutive_labs": boolean or null,
    "parallel_labs": boolean or null
  }},
  "action": {{
    "type": "UPSERT_TEACHER_CONSTRAINT" | null,
    "params": object or null
  }}
}}

Current config:
- max_daily_load: {current_config.get('max_daily_load', 4)}
- minimize_gaps: {current_config.get('minimize_gaps', False)}
- consecutive_labs: {current_config.get('consecutive_labs', True)}
- parallel_labs: {current_config.get('parallel_labs', True)}

Supported actions:
- Update config values when the user asks for max load, gaps, consecutive labs, or parallel labs.
- For teacher availability, use UPSERT_TEACHER_CONSTRAINT with params:
  teacher_name, day_of_week, start_time, end_time, is_available.
  Times must be HH:MM.
- Do not invent timetable moves here; those are handled by local move parsers.

{knowledge}
User message: {message}
"""
        parsed = self.ollama.generate_json(prompt, timeout=25.0)
        if not parsed:
            return self._local_chat_fallback(message, "Ollama did not respond with valid JSON in time.")

        return {
            "response": parsed.get("response") or "Updated from Ollama.",
            "updated_config": parsed.get("updated_config"),
            "action": parsed.get("action"),
        }

    def process_chat_request(self, message: str, current_config: Dict[str, Any], db=None) -> Dict[str, Any]:
        """
        Process a chat message regarding scheduling rules and entity info.
        """
        local_result = self._local_chat_fallback(message)
        if local_result.get("updated_config") is not None:
            return local_result

        if self._is_vague_conflict_followup(message):
            return {
                "response": (
                    "I need the original move details to fix conflicts. If the requested day is full, "
                    "say something like: move TY B sessions from Wednesday to other days."
                ),
                "updated_config": None,
                "action": None,
            }

        timetable_action = self.parse_timetable_action(message, db=db)
        if timetable_action:
            return {
                "response": "I understood this as a timetable move request.",
                "updated_config": None,
                "action": timetable_action,
            }

        lower_msg = message.lower()
        if any(word in lower_msg for word in ("remove", "move", "shift", "session", "class", "lecture", "lab")):
            return local_result

        return self._process_chat_with_ollama(message, current_config, db=db)
