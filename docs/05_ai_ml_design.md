# AI and Local NLP Design

## 1. Local-First AI Strategy

The assistant uses a local-first design:

1. Deterministic parsers handle frequent commands with low latency.
2. Ollama handles broader natural-language requests that cannot be parsed locally.
3. The backend never depends on a cloud LLM provider for normal AI assistant behavior.

This avoids external quota failures and keeps timetable-edit commands fast.

## 2. Ollama Integration

Implementation:
- `backend/app/services/llm/ollama_client.py`
- `backend/app/services/llm/nlp_service.py`

Default configuration:

```env
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.1
```

`OllamaClient.generate_json()` calls `/api/chat` with:
- `stream: false`
- `format: json`
- `temperature: 0`
- `num_predict: 256`
- bounded HTTP timeout

The service expects structured JSON so the backend can safely convert responses into app actions.

## 3. Deterministic Timetable Command Parser

The local parser handles commands such as:

```text
move TY B sessions from Wednesday to Saturday
from TY B remove the session from Wednsday and shift it other day
remove classes of Prof Sharma from Monday
```

Supported actions:
- `MOVE_GROUP_DAY_SESSIONS`
- `MOVE_TEACHER_DAY_SESSIONS`
- `UPSERT_TEACHER_CONSTRAINT` through the general NLP action path

Parser safeguards:
- Common day misspellings are normalized.
- Commands with missing context do not burn LLM calls.
- Follow-up commands such as "fix them" are resolved from frontend-held proposal context.

## 4. Timetable Change Service

Implementation:
- `backend/app/services/timetable_change_service.py`

Responsibilities:
- Find existing timetable entries by group/teacher and source day.
- Find compatible target slots.
- Reject room, teacher, group, and batch conflicts.
- Build a proposal before applying changes.
- Re-check proposed moves during apply to avoid stale writes.
- Save applied changes into `timetable_entries`.

The service uses proposal/apply separation so the frontend can show exactly what will move before the database is changed.

## 5. AI Assistant UI

Implementation:
- `frontend/src/components/ConstraintChatbot.tsx`

Behavior:
- Displays user and assistant messages.
- Shows proposed timetable moves in a confirmation panel.
- Applies accepted proposals through `/api/v1/ai/apply-timetable-change`.
- Signals the timetable page to refresh after a successful apply.
- Explains when generator preferences require a fresh timetable generation.

## 6. Machine Learning Module

The project includes optional ML scaffolding under:
- `backend/app/services/ml/`

Intended use:
- Learn from manual timetable edits and override reasons.
- Train a model to predict high-friction assignments.
- Convert predicted friction into soft-constraint penalty weights.

Current production scheduling still relies on OR-Tools CP-SAT plus deterministic soft constraints.
