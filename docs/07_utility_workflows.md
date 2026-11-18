# Utility Workflows

### 1. Master Data Entry
1. **User**: Admin logs in, navigates to "Teachers" or "Data Entry".
2. **UI**: Displays `DataTable` of records.
3. **Action**: Click "Add Teacher".
4. **Form**: Opens `Dialog` containing a form.
5. **Validation**: Frontend (React Hook Form) checks required fields.
6. **Submit**: `POST /api/v1/teachers`.
7. **Update**: Axios/fetch request succeeds, UI invalidates local state/fetches updated list.

### 2. Timetable Solver Run
1. **User**: Navigates to "Timetables" tab.
2. **Action**: Configures parameters (AI Soft Constraints) and clicks "Generate Timetable".
3. **Frontend**: Calls `POST /api/v1/solver/generate`.
4. **Backend**:
    - Receives `SolverConfig`.
    - If `SOLVER_ASYNC` is enabled, pushes task to Celery/Redis.
    - If synchronous (default for local), runs solver inline.
5. **Solver Engine**:
    - Pre-fetches all current data (Teachers, Rooms, Courses, Groups).
    - Constructs Boolean variables (`x[course, batch, teacher, room, slot]`).
    - Applies hard constraints (Teacher conflicts, consecutive labs).
    - Solves with Google OR-Tools.
    - Saves results to PostgreSQL (`timetable_entries`).
6. **Frontend**: Receives completion status and re-fetches grid data.

### 3. Bulk Import Workflow
1. **User**: Navigates to "Data Entry" tab.
2. **Action**: Uploads a CSV/JSON file or pastes raw text.
3. **Frontend**: Calls `POST /api/v1/imports/`.
4. **Backend**:
    - Parses JSON/CSV data.
    - Validates schema structure.
    - Performs bulk `INSERT` or `UPSERT` via SQLAlchemy.
5. **Result**: Entire database is seeded rapidly for testing or production start.

### 4. AI Chat (Ollama) Workflow
1. **User**: Opens the "Constraints" tab and types into the AI Assistant widget.
2. **Action**: User types: "Increase max daily load to 8".
3. **Frontend**: Sends `{ message, current_config }` to `POST /api/v1/ai/chat`.
4. **Backend**:
    - First tries deterministic local parsing for fast commands.
    - Uses Ollama only when local parsing cannot answer a general NLP request.
    - Constructs a prompt injecting DB context (known teachers, rooms).
    - Ollama returns a structured JSON instruction.
5. **Frontend**:
    - Displays AI response bubble.
    - Auto-applies configuration changes to the UI state.
