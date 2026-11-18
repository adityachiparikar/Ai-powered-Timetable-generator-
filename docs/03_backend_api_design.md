# Backend API Design
## FastAPI Structure

All routes are prefixed with `/api/v1`.

### 1. Auth (`/api/v1/login`)
- `POST /access-token`: JWT Token (OAuth2 password flow).
- Auth is bypassed in dev mode via `deps.py` returning a default admin user.

### 2. Teachers (`/api/v1/teachers`)
- `GET /` — List all teachers
- `POST /` — Create teacher
- `PUT /{id}` — Update teacher
- `DELETE /{id}` — Delete teacher

### 3. Courses (`/api/v1/courses`)
- `GET /` — List all courses (with type filter)
- `POST /` — Create course
- `PUT /{id}` — Update course
- `DELETE /{id}` — Delete course

### 4. Student Groups (`/api/v1/student-groups`)
- `GET /` — List groups with nested batches
- `POST /` — Create group
- `PUT /{id}` — Update group
- `DELETE /{id}` — Delete group
- Batch management integrated (batches auto-created with groups)

### 5. Rooms (`/api/v1/rooms`)
- `GET /` — List rooms
- `POST /` — Create room (with `is_lab` flag)
- `PUT /{id}` — Update room
- `DELETE /{id}` — Delete room

### 6. Breaks (`/api/v1/breaks`)
- Manages break slots in the timetable grid

### 7. Imports (`/api/v1/imports`)
- `POST /` — Bulk import of teachers, courses, rooms, groups from structured data

### 8. Solver (`/api/v1/solver`)
- `POST /generate` — Trigger timetable generation
    - Body: `SolverConfig` (max_time_seconds, consecutive_labs, parallel_labs, etc.)
    - Runs inline or via Celery based on `SOLVER_ASYNC` env var
    - Returns: `{ message, task_id, status?, result? }`
- `GET /status/{task_id}` — Poll async solver status
- `GET /logs/{task_id}` — Get solver run logs
- `GET /timetable/{term}` — Get saved timetable entries for a term

### 9. AI (`/api/v1/ai`)
- `POST /chat` — Chat with AI Assistant (local parser + Ollama)
    - Body: `{ message: str, current_config: dict }`
    - Returns: `{ response, updated_config, action }`
    - Can trigger `UPSERT_TEACHER_CONSTRAINT` actions
- `POST /parse` — Parse natural language constraint text
    - Body: `{ text: str }`
    - Returns structured JSON constraint

## Authentication
- **JWT Bearer tokens** via OAuth2 password flow
- **Dev mode**: Auth bypassed — `get_current_user()` returns a default admin
- **Dependency injection**: `Depends(deps.get_current_active_superuser)`

## Schemas (Pydantic v2)

```python
class SolverConfig(BaseModel):
    max_time_seconds: int = 120
    enable_soft_constraints: bool = True
    consecutive_labs: bool = True
    parallel_labs: bool = True
    max_daily_load: int = 6
    minimize_gaps: bool = False

class SolutionEntry(BaseModel):
    course_id: UUID
    course_code: str
    student_group: str
    course_type: Optional[str]
    batch_id: Optional[UUID]
    teacher_id: UUID
    room_id: UUID
    room: str
    time_slot_id: UUID
    day: str
    time_range: str
```
