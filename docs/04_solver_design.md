# Solver Design
## OR-Tools CP-SAT Formulation
**Implementation**: `backend/app/services/solver/engine.py`

### 1. Decision Variables
```python
x[course_id, batch_id, teacher_id, room_id, slot_id] ∈ {0, 1}
```
- **Theory courses**: `batch_id = None`, applies to entire student group.
- **Lab/Tutorial courses**: One variable set per batch (e.g., B1, B2, B3).
- **Pre-filtering**: Only rooms with sufficient capacity and correct type (lab/classroom) are considered, reducing the variable count significantly.

### 2. Unit Decomposition
Each course is broken into "Units" — the atomic scheduling unit:
- **Theory** → 1 unit per group (batch = None)
- **Lab/Tutorial** → 1 unit per batch (e.g., 3 batches = 3 independent units)

Each unit tracks:
- `slot_indicators`: Boolean per time slot (is this unit active at slot S?)
- `required_sessions`: Number of weekly slots needed

### 3. Hard Constraints (Must Satisfy)

#### A. Teacher Conflict
```python
# A teacher can only teach one session per slot
model.Add(sum(vars_by_teacher[t][s]) <= 1)  ∀ t, s
```

#### B. Room Conflict
```python
# A room can only host one session per slot
model.Add(sum(vars_by_room[r][s]) <= 1)  ∀ r, s
```

#### C. Batch Independence
```python
# A batch cannot attend two different sessions simultaneously
model.Add(sum(vars_by_batch[b][s]) <= 1)  ∀ b, s
```

#### D. Group-Batch Synchronization
```python
# If a Theory session is active for Group G at slot S,
# no batch of Group G can have a Lab at slot S
model.Add(sum(batch_vars) + sum(theory_vars) <= 1)  ∀ batch ∈ group, s
```

#### E. Theory Mutual Exclusion
```python
# Only one Theory course per group per slot
model.Add(sum(vars_by_group_theory[g][s]) <= 1)  ∀ g, s
```

#### F. At Most One Room Per Slot Per Unit
```python
model.Add(sum(room_vars_for_slot) <= 1)
```

#### G. Exact Session Count
```python
model.Add(sum(slot_used_vars) == sessions_count)
```

#### H. Consecutive 2-Hour Lab Blocks
```python
# Every active lab slot must have at least 1 temporally contiguous neighbor
model.Add(slot_indicator[S] <= slot_indicator[S-1] + slot_indicator[S+1])
```
- Temporal gap check: `prev_slot.end_time == slot.start_time`
- Same-room enforcement: The same room variable constraint is applied

#### I. Teacher Availability
```python
# If teacher is busy during [start, end], force vars to 0
if slot in busy_range:
    model.Add(sum(slot_vars) == 0)
```

### 4. Soft Constraints (Objective Function)
```python
Minimize Σ penalties
```

#### A. Lab Parallelism (weight: 500)
```python
# Penalty if some (but not all) batches of a group are active at a slot
penalties.append(partial_sync * 500)
```

#### B. Teacher Daily Load (weight: 10)
```python
# Penalty for exceeding max_daily_load (default: 6)
excess = load - limit
penalties.append(excess * 10)
```

#### C. Gap Minimization
- Placeholder for future implementation
- Currently relies on other constraints for schedule compactness

### 5. Solver Configuration
```python
class SolverConfig:
    max_time_seconds: int = 120
    enable_soft_constraints: bool = True
    consecutive_labs: bool = True
    parallel_labs: bool = True
    max_daily_load: int = 6
    minimize_gaps: bool = False
```

### 6. Output
The solver returns `SolverOutput`:
- `status`: OPTIMAL | FEASIBLE | INFEASIBLE | UNKNOWN
- `score`: Objective function value
- `entries`: List of `SolutionEntry` with course, room, day, time assignments

### 7. Performance
| Metric | Value |
|---|---|
| Variables | ~118,800 (sparse) |
| Constraints | ~15,000+ |
| Typical solve time | < 30 seconds |
| Timeout | 120s (configurable) |
