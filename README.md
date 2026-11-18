# AI-Driven University Timetable Generator

A production-grade system to generate conflict-free university schedules using Constraint Programming (Google OR-Tools) and Machine Learning constraints.

## Features
- **AI Solver**: Uses CP-SAT to ensure no hard constraint violations (double bookings, room capacity).
- **Smart Scheduling**: Optimizes for teacher preferences and load balancing.
- **Interactive UI**: Drag-and-drop grid (React + Tailwind).
- **Master Data**: Manage Teachers, Courses, Rooms via Admin Dashboard.

## Methodology

### 1. Mathematical Formulation
The timetable generation is modeled as a **Constraint Satisfaction Problem (CSP)**. We define boolean decision variables $x_{c,b,t,r,s}$ where:
- $c$: Course
- $b$: Student Batch
- $t$: Teacher
- $r$: Room
- $s$: Time Slot

### 2. Constraint Engine
The system utilizes the **Google OR-Tools CP-SAT Solver** to find a valid assignment that satisfies all hard constraints while minimizing a penalty function for soft constraints.

**Hard Constraints:**
- **Teacher Availability:** No teacher assigned to multiple sessions simultaneously.
- **Room Uniqueness:** No room host multiple sessions simultaneously.
- **Student Synchronization:** A student batch cannot attend multiple sessions at once.
- **Consecutive Blocks:** Lab sessions are forced into contiguous 2-hour blocks in the same room.

**Soft Constraints (Optimization):**
- **Lab Parallelism:** Encouraging batches of the same group to have labs simultaneously.
- **Workload Balance:** Penalizing excessive daily teaching hours.
- **Gap Minimization:** Reducing idle time for students and faculty.

### 3. Asynchronous Workflow
1. **Data Hydration:** Backend extracts and indexes all relevant entities.
2. **Constraint Mapping:** The solver constructs thousands of boolean variables and constraints.
3. **Solving:** Parallel search explores the solution space with a configurable timeout.
4. **Persistence:** Optimal results are committed to PostgreSQL and streamed to the UI via Redis.

## Setup & Run

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL
- Redis (for Worker)

### Setup Steps
1.  **Database Setup**
    - Ensure PostgreSQL is running.
    - Create a database (e.g., `timetable_db`).
    - Update `.env` with your credentials.

2.  **Redis Setup (Required for AI Solver)**
    - **Automatic (Windows):** I've included a portable Redis in the `redis/` folder.
    - Run `scripts/start_redis.ps1` to start the Redis server.
    - Ensure Redis is running *before* starting the worker.

3.  **Install Dependencies**
    - Backend:
      ```bash
      cd backend
      python -m venv venv
      .\venv\Scripts\activate
      pip install -r requirements.txt
      ```
    - Frontend:
      ```bash
      cd frontend
      npm install
      ```

### Quick Start (Windows)
1.  **Start Backend**:
    ```powershell
    .\scripts\start_backend.ps1
    ```
    *This runs database migrations and starts the FastAPI server on localhost:8000*

2.  **Start Frontend**:
    ```powershell
    .\scripts\start_frontend.ps1
    ```
    *Access the UI at localhost:5173*

3.  **Start AI Worker** (Optional - for background solver):
    In a new terminal:
    ```powershell
    .\scripts\start_worker.ps1
    ```

## Architecture
- **Backend API**: FastAPI (`/backend`)
- **Frontend**: React + shadcn/ui (`/frontend`)
- **Solver**: OR-Tools + Celery (`/worker`)
- **Database**: PostgreSQL

## Configuration

### API Keys & Environment Variables
Create a `.env` file in the `backend/` directory:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/timetable_db

# Redis (for Celery)
REDIS_URL=redis://localhost:6379/0

# Local Ollama LLM (for NLP features)
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.1

# JWT Secret
SECRET_KEY=your_secret_key_here
```

**Ollama setup:**
1. Install and start Ollama.
2. Pull the model: `ollama pull llama3.1`
3. Keep Ollama running on `http://127.0.0.1:11434`.

### ML Dataset Setup
The ML component learns soft constraint weights from historical timetable data.

**Dataset Format:**
Place CSV files in `backend/data/historical/`:

```csv
# constraint_logs.csv
teacher_id,course_id,slot_id,room_id,user_satisfaction,override_reason
teacher_1,course_math,slot_mon_9am,room_101,0.8,preferred_morning_slot
teacher_2,course_physics,slot_fri_2pm,room_lab1,0.3,too_late_in_week
```

**Training the ML Model:**
```powershell
cd backend
.\venv\Scripts\activate
python -m app.services.ml.trainer
```

The trained model will be saved to `backend/models/` and used by the solver to optimize soft constraints.

## Development
- **Tests**: `pytest backend/tests`
- **Linting**: `npm run lint` (frontend)
- **Database Migrations**: `cd backend && alembic revision --autogenerate -m "description" && alembic upgrade head`
