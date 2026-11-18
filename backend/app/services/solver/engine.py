from ortools.sat.python import cp_model
from typing import List, Dict, Any, Tuple, Optional
from uuid import UUID

from app.services.solver.data_wrapper import SolverDataWrapper
from app.schemas.solver import SolverConfig, SolverOutput, SolutionEntry
from app.models import CourseType

class TimetableSolver:
    def __init__(self, wrapper: SolverDataWrapper, config: SolverConfig):
        self.wrapper = wrapper
        self.config = config
        self.model = cp_model.CpModel()
        
        # Lookups
        self.slot_map = {s.id: s for s in self.wrapper.slots}
        self.teacher_map = {t.id: t for t in self.wrapper.teachers}
        self.course_map = {c.id: c for c in self.wrapper.courses}
        self.room_map = {r.id: r for r in self.wrapper.rooms}
        self.group_map = {g.id: g for g in self.wrapper.groups}
        
        # Variables configuration
        self.vars: Dict[Tuple[UUID, Optional[UUID], UUID, UUID, int], cp_model.IntVar] = {}
        self.vars_by_teacher: Dict[UUID, Dict[int, List[cp_model.IntVar]]] = {}
        self.vars_by_room: Dict[UUID, Dict[int, List[cp_model.IntVar]]] = {}
        self.vars_by_group_theory: Dict[UUID, Dict[int, List[cp_model.IntVar]]] = {}
        self.vars_by_batch: Dict[UUID, Dict[int, List[cp_model.IntVar]]] = {}
        self.vars_by_unit: Dict[Tuple[UUID, Optional[UUID]], Dict[UUID, List[cp_model.IntVar]]] = {}
        self.vars_by_unit_room: Dict[Tuple[UUID, Optional[UUID], UUID, UUID], Dict[UUID, cp_model.IntVar]] = {}
        self.unit_metadata: Dict[Tuple[UUID, Optional[UUID]], Dict[str, Any]] = {}
        
        # Batch Parent Mapping
        self.batch_parent_map: Dict[UUID, UUID] = {} # batch_id -> group_id
        for group in self.wrapper.groups:
            if group.batches:
                for b in group.batches:
                    self.batch_parent_map[b.id] = group.id

    def create_variables(self, course_allocations: List[Dict]):
        for alloc in course_allocations:
            course = alloc['course']
            group_id = alloc['group_id']
            batches = alloc.get('batches', []) 
            teacher_id = alloc['teacher_id']
            sessions_count = alloc.get('sessions', course.weekly_sessions)
            
            # Resolve group object first
            group_obj = self.group_map.get(group_id)

            # If Lab/Tutorial and no batches specified, fetch all batches for the group
            if course.course_type in [CourseType.LAB, CourseType.TUTORIAL] and not batches and group_obj:
                 # Helper to ensure we have a list of batches
                 batches = list(group_obj.batches) if group_obj.batches else []

            # Register Batches to Parent for later lookup
            for b in batches:
                self.batch_parent_map[b.id] = group_id

            # Decide units
            units = [] # List of (batch_id_or_none, required_size)
            if course.course_type == CourseType.THEORY:
                # Theory -> Null batch
                size = group_obj.size if group_obj else 0
                units.append((None, size))
                
                # We do not want to iterate over `batches` and create variables
                # for them if this is a THEORY course.
                # Theory courses apply to the whole group, not individual batches.
            else:
                # Lab/Tutorial -> Specific Batches
                for b in batches:
                    units.append((b.id, b.size))

            for batch_id, req_size in units:
                valid_rooms = [r for r in self.wrapper.rooms if (r.capacity or 0) >= (req_size or 0)]
                if course.course_type == CourseType.LAB:
                    valid_rooms = [r for r in valid_rooms if r.is_lab]
                elif course.course_type == CourseType.TUTORIAL:
                    valid_rooms = [r for r in valid_rooms if r.is_tutorial_room]
                else:
                    valid_rooms = [r for r in valid_rooms if not r.is_lab and not r.is_tutorial_room]

                unit_vars = []
                for room in valid_rooms:
                    for slot in self.wrapper.slots:
                        # Include room.id in name so every var has a unique CP-SAT name
                        var_name = f"x_{course.code}_{batch_id}_{room.id}_{slot.id}"
                        x = self.model.NewBoolVar(var_name)
                        
                        key = (course.id, batch_id, teacher_id, room.id, slot.id)
                        self.vars[key] = x
                        unit_vars.append(x)
                        
                        # Helpers
                        self.vars_by_teacher.setdefault(teacher_id, {}).setdefault(slot.id, []).append(x)
                        self.vars_by_room.setdefault(room.id, {}).setdefault(slot.id, []).append(x)
                        
                        if batch_id is None:
                            # Theory Var
                            self.vars_by_group_theory.setdefault(group_id, {}).setdefault(slot.id, []).append(x)
                        else:
                            # Batch Var
                            self.vars_by_batch.setdefault(batch_id, {}).setdefault(slot.id, []).append(x)
                        
                        # Unit tracking for consecutive constraints
                        unit_key = (course.id, batch_id)
                        self.vars_by_unit.setdefault(unit_key, {}).setdefault(slot.id, []).append(x)
                        
                        # Room-specific unit tracking for same-room consecutive constraints
                        unit_room_key = (course.id, batch_id, teacher_id, room.id)
                        self.vars_by_unit_room.setdefault(unit_room_key, {})[slot.id] = x

                if unit_vars:
                    unit_key = (course.id, batch_id)
                    slot_used_vars = []

                    for slot in self.wrapper.slots:
                        room_vars_for_slot = self.vars_by_unit.get(unit_key, {}).get(slot.id, [])
                        if not room_vars_for_slot:
                            continue

                        # At most 1 room chosen per slot for this course+batch
                        self.model.Add(sum(room_vars_for_slot) <= 1)

                        # slot_used = 1  iff  any room is chosen for this slot
                        slot_used = self.model.NewBoolVar(
                            f"su_{course.code}_{batch_id}_{slot.id}"
                        )
                        self.model.Add(sum(room_vars_for_slot) == slot_used)
                        slot_used_vars.append(slot_used)
                        
                        # Store for consecutive logic
                        meta = self.unit_metadata.setdefault(unit_key, {})
                        meta.setdefault("slot_indicators", {})[slot.id] = slot_used
                    
                    self.unit_metadata[unit_key]["required_sessions"] = sessions_count

                    # Exactly sessions_count DISTINCT time slots must be scheduled
                    if slot_used_vars:
                        self.model.Add(sum(slot_used_vars) == sessions_count)
    
    def add_hard_constraints(self):
        # 1. Teacher Conflict
        for t_id, t_slots in self.vars_by_teacher.items():
            # Basic Conflict (one class at a time)
            for slot_vars in t_slots.values():
                self.model.Add(sum(slot_vars) <= 1)
            
            # Specific Teacher Availability Constraints (e.g. 8-4 Only)
            teacher_obj = self.teacher_map.get(t_id)
            if teacher_obj and hasattr(teacher_obj, 'specific_constraints'):
                for tc in teacher_obj.specific_constraints:
                    for s_id, slot_vars in t_slots.items():
                        slot = self.slot_map.get(s_id)
                        if not slot: continue
                        
                        # logic: if this slot is outside allowed range, force sum(vars) == 0
                        is_match = False
                        if not tc.day_of_week or slot.day_of_week.lower() == tc.day_of_week.lower():
                            if tc.start_time and tc.end_time:
                                # Busy during [start, end].
                                if not tc.is_available:
                                    if slot.start_time >= tc.start_time and slot.end_time <= tc.end_time:
                                        is_match = True
                                else:
                                    # Available ONLY during [start, end].
                                    if slot.start_time < tc.start_time or slot.end_time > tc.end_time:
                                        is_match = True
                        
                        if is_match:
                            self.model.Add(sum(slot_vars) == 0)

        # 2. Room Conflict
        for r_slots in self.vars_by_room.values():
            for slot_vars in r_slots.values():
                self.model.Add(sum(slot_vars) <= 1)

        # 3. Batch Conflict (Independent)
        # Ensure no batch is assigned more than one session at a time
        for batch_id, b_slots in self.vars_by_batch.items():
            for s_id, batch_vars in b_slots.items():
                self.model.Add(sum(batch_vars) <= 1)

        # 4. Group/Batch Conflict (Sync between Batch and Theory)
        for batch_id, b_slots in self.vars_by_batch.items():
            parent_group_id = self.batch_parent_map.get(batch_id)
            if not parent_group_id: continue
            
            # If the batch's parent group has theory sessions, they cannot overlap
            if parent_group_id in self.vars_by_group_theory:
                for s_id, batch_vars in b_slots.items():
                    theory_vars = self.vars_by_group_theory[parent_group_id].get(s_id, [])
                    if theory_vars:
                         self.model.Add(sum(batch_vars) + sum(theory_vars) <= 1)

        # 4. Pure Theory Conflict (Multiple theories for same group)
        for g_slots in self.vars_by_group_theory.values():
            for slot_vars in g_slots.values():
                self.model.Add(sum(slot_vars) <= 1)
        
        # 5. Pure Batch Conflict (Batch A1 cannot have 2 labs at once)
        # Covered by Step 3's logic
        
        # 6. Consecutive 2-Hour Labs
        if self.config.consecutive_labs:
            self._add_consecutive_lab_constraints()

        # 7. Keep each division's active days compact and avoid late-only days.
        if self.config.max_group_gap_hours is not None:
            self._add_group_long_gap_constraints()

    def _add_consecutive_lab_constraints(self):
        # We need to map time slot IDs to their actual objects to check for continuity
        slot_map = {s.id: s for s in self.wrapper.slots}
        
        # Group slots by day and sort by time
        day_slots = {}
        for s in self.wrapper.slots:
            day_slots.setdefault(s.day_of_week, []).append(s)
        
        for d in day_slots:
            day_slots[d].sort(key=lambda x: x.start_time)

        # 1. Ensure each unit (course+batch) has consecutive slots for LAB/TUTORIAL
        for (course_id, batch_id), slot_vars_dict in self.vars_by_unit.items():
            course = self.course_map.get(course_id)
            if not course or course.course_type not in [CourseType.LAB, CourseType.TUTORIAL]:
                continue
            
            unit_key = (course_id, batch_id)
            meta = self.unit_metadata.get(unit_key, {})
            req_sessions = meta.get("required_sessions", 0)
            if req_sessions <= 1:
                continue

            slot_indicators = meta.get("slot_indicators", {})
            if not slot_indicators:
                continue

            for s_id, slot_indicator in slot_indicators.items():
                slot = slot_map[s_id]
                day = slot.day_of_week
                slots_in_day = day_slots[day]
                idx = slots_in_day.index(slot)
                
                prev_slot = slots_in_day[idx-1] if idx > 0 else None
                next_slot = slots_in_day[idx+1] if idx < len(slots_in_day)-1 else None
                
                # Check for temporal gaps (e.g. 10-11 and 12-13 is not consecutive)
                x_prev = 0
                if prev_slot and prev_slot.end_time == slot.start_time:
                    x_prev = slot_indicators.get(prev_slot.id, 0)
                
                x_next = 0
                if next_slot and next_slot.start_time == slot.end_time:
                    x_next = slot_indicators.get(next_slot.id, 0)
                
                # Hard Constraint: Every active slot must have at least 1 temporally consecutive neighbor
                # This forces blocks of at least 2 hours.
                self.model.Add(slot_indicator <= x_prev + x_next)

        # 2. Second, force the SAME room for these consecutive slots
        for (c_id, b_id, t_id, r_id), slots_in_unit_room in self.vars_by_unit_room.items():
            course = self.course_map.get(c_id)
            if not course or course.course_type not in [CourseType.LAB, CourseType.TUTORIAL]:
                continue
            
            unit_key = (c_id, b_id)
            meta = self.unit_metadata.get(unit_key, {})
            req_sessions = meta.get("required_sessions", 0)
            if req_sessions <= 1:
                continue

            for s_id, x_s_r in slots_in_unit_room.items():
                slot = slot_map[s_id]
                day = slot.day_of_week
                slots_in_day = day_slots[day]
                idx = slots_in_day.index(slot)
                
                prev_slot = slots_in_day[idx-1] if idx > 0 else None
                next_slot = slots_in_day[idx+1] if idx < len(slots_in_day)-1 else None
                
                x_prev_r = 0
                if prev_slot and prev_slot.end_time == slot.start_time:
                    x_prev_r = slots_in_unit_room.get(prev_slot.id, 0)
                
                x_next_r = 0
                if next_slot and next_slot.start_time == slot.end_time:
                    x_next_r = slots_in_unit_room.get(next_slot.id, 0)
                
                # If scheduled in room r at slot s, must be in same room r at s-1 or s+1
                self.model.Add(x_s_r <= x_prev_r + x_next_r)

    def _add_group_long_gap_constraints(self):
        day_slots = self._slots_by_day()
        group_slot_vars: Dict[UUID, Dict[UUID, List[cp_model.IntVar]]] = {}

        for group_id, slots in self.vars_by_group_theory.items():
            for slot_id, vars_list in slots.items():
                group_slot_vars.setdefault(group_id, {}).setdefault(slot_id, []).extend(vars_list)

        for batch_id, slots in self.vars_by_batch.items():
            parent_group_id = self.batch_parent_map.get(batch_id)
            if not parent_group_id:
                continue
            for slot_id, vars_list in slots.items():
                group_slot_vars.setdefault(parent_group_id, {}).setdefault(slot_id, []).extend(vars_list)

        for group_id, slot_vars in group_slot_vars.items():
            for day, slots in day_slots.items():
                active_by_index: List[cp_model.IntVar] = []
                for slot in slots:
                    vars_in_slot = slot_vars.get(slot.id, [])
                    if not vars_in_slot:
                        active = self.model.NewConstant(0)
                    elif len(vars_in_slot) == 1:
                        active = vars_in_slot[0]
                    else:
                        active = self.model.NewBoolVar(f"group_active_{group_id}_{day}_{slot.id}")
                        self.model.Add(sum(vars_in_slot) >= 1).OnlyEnforceIf(active)
                        self.model.Add(sum(vars_in_slot) == 0).OnlyEnforceIf(active.Not())
                    active_by_index.append(active)

                max_gap_slots = max(0, self.config.max_group_gap_hours)
                big_m = len(active_by_index)

                # If a division has any class after 10:00, it must also have
                # at least one class in the first three teaching slots. This
                # avoids late-only days while staying feasible for heavy loads.
                early_window = active_by_index[:3]
                if early_window:
                    early_activity = sum(early_window)
                    for j in range(3, len(active_by_index)):
                        self.model.Add(active_by_index[j] <= early_activity)

                # Between the first and last active slot of a division's day,
                # total empty teaching slots cannot exceed max_gap_slots.
                for i in range(len(active_by_index)):
                    for j in range(i + 2, len(active_by_index)):
                        middle = active_by_index[i + 1:j]
                        gap_slots = j - i - 1
                        if gap_slots <= max_gap_slots:
                            continue

                        self.model.Add(
                            sum(middle) >= gap_slots - max_gap_slots - big_m * (2 - active_by_index[i] - active_by_index[j])
                        )

    def add_soft_constraints(self):
        if not self.config.enable_soft_constraints:
            return

        penalties = []
        
        # 1. Lab Synchronization (Parallelism)
        if self.config.parallel_labs:
            group_to_batches = {}
            for b_id, slot_vars in self.vars_by_batch.items():
                pg_id = self.batch_parent_map.get(b_id)
                if pg_id:
                    group_to_batches.setdefault(pg_id, []).append(slot_vars)

            for pg_id, batches_slots_list in group_to_batches.items():
                if len(batches_slots_list) < 2: continue
                
                all_s_ids = set()
                for b_slots in batches_slots_list:
                    all_s_ids.update(b_slots.keys())
                    
                for s_id in all_s_ids:
                    batch_activity = [sum(b_slots.get(s_id, [])) for b_slots in batches_slots_list]
                    total_active = self.model.NewIntVar(0, len(batches_slots_list), f"sync_{pg_id}_{s_id}")
                    self.model.Add(total_active == sum(batch_activity))

                    is_any_active = self.model.NewBoolVar(f"any_active_{pg_id}_{s_id}")
                    self.model.Add(total_active > 0).OnlyEnforceIf(is_any_active)
                    self.model.Add(total_active == 0).OnlyEnforceIf(is_any_active.Not())
                    
                    is_fully_synced = self.model.NewBoolVar(f"full_sync_{pg_id}_{s_id}")
                    self.model.Add(total_active == len(batches_slots_list)).OnlyEnforceIf(is_fully_synced)
                    self.model.Add(total_active < len(batches_slots_list)).OnlyEnforceIf(is_fully_synced.Not())
                    
                    # Penalty: Is active but NOT fully synced
                    partial_sync = self.model.NewBoolVar(f"partial_sync_{pg_id}_{s_id}")
                    self.model.Add(partial_sync == 1).OnlyEnforceIf([is_any_active, is_fully_synced.Not()])
                    self.model.Add(partial_sync == 0).OnlyEnforceIf(is_any_active.Not())
                    self.model.Add(partial_sync == 0).OnlyEnforceIf(is_fully_synced)
                    
                    penalties.append(partial_sync * 500) 

        # 2. Max Daily Load per Teacher
        limit_load = self.config.max_daily_load
        for t_id, t_slots in self.vars_by_teacher.items():
            daily_vars = {} 
            for s_id, vars_list in t_slots.items():
                slot = next((s for s in self.wrapper.slots if s.id == s_id), None)
                if slot:
                    daily_vars.setdefault(slot.day_of_week, []).extend(vars_list)
            
            for day, vars_in_day in daily_vars.items():
                load = sum(vars_in_day)
                excess = self.model.NewIntVar(0, 10, f"excess_load_{t_id}_{day}")
                self.model.Add(excess >= load - limit_load)
                penalties.append(excess * 10)

        # 3. Minimize Gaps / Random Spread
        if self.config.minimize_gaps:
            penalties.extend(self._build_compactness_penalties())

        if penalties:
            self.model.Minimize(sum(penalties))

    def _build_compactness_penalties(self) -> List[cp_model.LinearExpr]:
        penalties: List[cp_model.LinearExpr] = []
        day_slots = self._slots_by_day()

        for teacher_id, slot_vars in self.vars_by_teacher.items():
            penalties.extend(
                self._entity_compactness_penalties(
                    f"teacher_{teacher_id}",
                    slot_vars,
                    day_slots,
                    weight=25,
                )
            )

        group_slot_vars: Dict[UUID, Dict[int, List[cp_model.IntVar]]] = {}
        for group_id, slots in self.vars_by_group_theory.items():
            for slot_id, vars_list in slots.items():
                group_slot_vars.setdefault(group_id, {}).setdefault(slot_id, []).extend(vars_list)

        for batch_id, slots in self.vars_by_batch.items():
            parent_group_id = self.batch_parent_map.get(batch_id)
            if not parent_group_id:
                continue
            for slot_id, vars_list in slots.items():
                group_slot_vars.setdefault(parent_group_id, {}).setdefault(slot_id, []).extend(vars_list)

        for group_id, slot_vars in group_slot_vars.items():
            penalties.extend(
                self._entity_compactness_penalties(
                    f"group_{group_id}",
                    slot_vars,
                    day_slots,
                    weight=40,
                )
            )

        return penalties

    def _entity_compactness_penalties(
        self,
        prefix: str,
        slot_vars: Dict[UUID, List[cp_model.IntVar]],
        day_slots: Dict[str, List[Any]],
        weight: int,
    ) -> List[cp_model.LinearExpr]:
        penalties: List[cp_model.LinearExpr] = []

        for day, slots in day_slots.items():
            active_by_index: List[cp_model.IntVar] = []
            for slot in slots:
                vars_in_slot = slot_vars.get(slot.id, [])
                if not vars_in_slot:
                    active = self.model.NewConstant(0)
                elif len(vars_in_slot) == 1:
                    active = vars_in_slot[0]
                else:
                    active = self.model.NewBoolVar(f"active_{prefix}_{day}_{slot.id}")
                    self.model.Add(sum(vars_in_slot) >= 1).OnlyEnforceIf(active)
                    self.model.Add(sum(vars_in_slot) == 0).OnlyEnforceIf(active.Not())
                active_by_index.append(active)

            for i in range(len(active_by_index)):
                max_j = min(len(active_by_index), i + 5)
                for j in range(i + 2, max_j):
                    pair_active = self.model.NewBoolVar(f"spread_{prefix}_{day}_{i}_{j}")
                    self.model.Add(pair_active <= active_by_index[i])
                    self.model.Add(pair_active <= active_by_index[j])
                    self.model.Add(pair_active >= active_by_index[i] + active_by_index[j] - 1)
                    gap_slots = j - i - 1
                    penalties.append(pair_active * weight * gap_slots)

        return penalties

    def _slots_by_day(self) -> Dict[str, List[Any]]:
        day_slots: Dict[str, List[Any]] = {}
        for slot in self.wrapper.slots:
            day_slots.setdefault(slot.day_of_week, []).append(slot)
        for slots in day_slots.values():
            slots.sort(key=lambda slot: slot.start_time)
        return day_slots


    def solve(self) -> SolverOutput:
        self._add_early_slot_search_strategy()
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = self.config.max_time_seconds
        solver.parameters.num_search_workers = self.config.num_workers
        status_val = solver.Solve(self.model)
        
        status_map = {
            cp_model.OPTIMAL: "OPTIMAL",
            cp_model.FEASIBLE: "FEASIBLE",
            cp_model.INFEASIBLE: "INFEASIBLE",
            cp_model.MODEL_INVALID: "INVALID",
            cp_model.UNKNOWN: "UNKNOWN",
        }
        
        entries = []
        if status_val in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            # Create Lookups
            # Create Lookups
            slot_map = {s.id: s for s in self.wrapper.slots}
            course_map = {c.id: c for c in self.wrapper.courses}
            room_map = {r.id: r for r in self.wrapper.rooms}
            group_map = {g.id: g for g in self.wrapper.groups}

            for key, var in self.vars.items():
                if solver.Value(var) == 1:
                    c_id, b_id, t_id, r_id, s_id = key
                    slot = slot_map.get(s_id)
                    course = course_map.get(c_id)
                    room = room_map.get(r_id)
                    
                    # Resolve Group Name
                    group_name = "Unknown Group"
                    if course and course.student_group_id:
                        g_obj = group_map.get(course.student_group_id)
                        if g_obj: group_name = g_obj.name

                    # Format time as HH:MM
                    t_str = "Unknown"
                    day_str = "Unknown"
                    if slot:
                        day_str = slot.day_of_week
                        s_t = slot.start_time.strftime("%H:%M") if hasattr(slot.start_time, "strftime") else str(slot.start_time)
                        e_t = slot.end_time.strftime("%H:%M") if hasattr(slot.end_time, "strftime") else str(slot.end_time)
                        t_str = f"{s_t} - {e_t}"

                    entries.append(SolutionEntry(
                        course_id=c_id,
                        course_code=course.code if course else "UNK",
                        student_group=group_name,
                        course_type=course.course_type if course else None,
                        batch_id=b_id,
                        teacher_id=t_id,
                        room_id=r_id,
                        room=room.name if room else "Unknown Room",
                        time_slot_id=s_id,
                        day=day_str,
                        time_range=t_str
                    ))
        
        return SolverOutput(
            status=status_map[status_val],
            score=solver.ObjectiveValue(),
            entries=entries
        )

    def _add_early_slot_search_strategy(self):
        if not self.vars:
            return

        day_order = {
            "Monday": 0,
            "Tuesday": 1,
            "Wednesday": 2,
            "Thursday": 3,
            "Friday": 4,
            "Saturday": 5,
        }

        def sort_key(item):
            (_, _, _, _, slot_id), _ = item
            slot = self.slot_map.get(slot_id)
            if not slot:
                return (99, "99:99", str(slot_id))
            return (
                day_order.get(slot.day_of_week, 99),
                slot.start_time,
                str(slot_id),
            )

        ordered_vars = [var for _, var in sorted(self.vars.items(), key=sort_key)]
        self.model.AddDecisionStrategy(
            ordered_vars,
            cp_model.CHOOSE_FIRST,
            cp_model.SELECT_MAX_VALUE,
        )
