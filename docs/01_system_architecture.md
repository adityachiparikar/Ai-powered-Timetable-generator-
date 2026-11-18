# System Architecture & Design
## AI-Driven University Timetable Generator

### 1. High-Level Architecture
The system utilizes a modular architecture with three independently runnable services:
- **Frontend**: React SPA (Vite) serving as the interface for admin users.
- **Backend**: FastAPI server handling REST API requests, Auth (JWT), and Business Logic.
- **Worker**: Celery worker connected via Redis for CPU-intensive solver tasks.
- **Data Layer**: PostgreSQL for structured data, Redis for task queues and result caching.
- **AI Layer**: Local Ollama LLM for NLP chat, plus deterministic local parsers for common timetable commands.

### 2. Technology Stack
- **Backend**: Python 3.10+, FastAPI, SQLAlchemy, Alembic, Pydantic v2 (pydantic-settings).
- **Frontend**: TypeScript, React 18, Vite, Tailwind CSS, shadcn/ui, Lucide Icons.
- **Optimization**: Google OR-Tools (CP-SAT Solver).
- **ML/AI**: Ollama (`llama3.1` by default), deterministic NLP parsers, optional Scikit-Learn modules.
- **Infrastructure**: Docker Compose (optional), Redis, PostgreSQL.

### 3. Folder Structure
```
/root
├── /backend
│   ├── /app
│   │   ├── /api              # API Layer
│   │   │   ├── /endpoints    # Route handlers
│   │   │   │   ├── ai.py         # AI chat & NLP parsing
│   │   │   │   ├── courses.py    # Course CRUD
│   │   │   │   ├── imports.py    # Bulk data import
│   │   │   │   ├── login.py      # JWT authentication
│   │   │   │   ├── rooms.py      # Room CRUD
│   │   │   │   ├── breaks.py     # Break/slot management
│   │   │   │   ├── solver.py     # Solver trigger & status
│   │   │   │   ├── student_groups.py  # Group/Batch CRUD
│   │   │   │   └── teachers.py   # Teacher CRUD
│   │   │   ├── deps.py       # Dependencies (DB, Auth)
│   │   │   └── api.py        # Router aggregator
│   │   ├── /core             # Config, Security
│   │   │   ├── config.py     # Pydantic Settings (.env)
│   │   │   └── security.py   # JWT helpers
│   │   ├── /crud             # Database operations
│   │   ├── /db               # Database session/base
│   │   ├── /models           # SQLAlchemy ORM Models
│   │   ├── /schemas          # Pydantic Request/Response Schemas
│   │   ├── /services         # Business Logic
│   │   │   ├── /solver       # OR-Tools CP-SAT Engine
│   │   │   │   ├── engine.py       # Core solver (variables, constraints)
│   │   │   │   ├── data_wrapper.py # Data hydration layer
│   │   │   │   └── logger.py       # Solver run logging
│   │   │   ├── /llm          # Ollama AI Integration
│   │   │   │   ├── ollama_client.py # Ollama HTTP wrapper
│   │   │   │   └── nlp_service.py   # Chat & constraint parsing
│   │   │   ├── /ml           # Machine Learning
│   │   │   └── export_service.py
│   │   └── main.py           # FastAPI entry point
│   ├── /alembic              # Database migrations
│   ├── .env                  # Environment variables
│   ├── requirements.txt
│   └── venv/
├── /worker
│   ├── celery_app.py         # Celery configuration
│   └── /tasks
│       └── solver_task.py    # Background solver execution
├── /frontend
│   ├── /src
│   │   ├── /components       # Shared UI Components
│   │   │   ├── ConstraintChatbot.tsx  # AI Assistant widget
│   │   │   ├── /timetable    # Timetable grid components
│   │   │   └── /ui           # shadcn/ui primitives
│   │   ├── /pages            # Route pages
│   │   │   ├── Dashboard.tsx
│   │   │   ├── DataEntry.tsx
│   │   │   ├── Timetables.tsx
│   │   │   ├── Teachers.tsx
│   │   │   ├── Constraints.tsx
│   │   │   ├── Settings.tsx
│   │   │   └── Login.tsx
│   │   ├── /services         # API client (Axios)
│   │   ├── /lib              # Utilities
│   │   ├── /layouts          # Page layout wrappers
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
├── /docs                     # Design Documentation (this folder)
├── /scripts                  # PowerShell startup scripts
│   ├── start_backend.ps1
│   ├── start_frontend.ps1
│   └── start_worker.ps1
├── /redis                    # Portable Redis (Windows)
├── docker-compose.yml
└── README.md
```

### 4. Service Communication
```
[React Frontend :5173]
      │ (REST API / Axios)
      ▼
[FastAPI Backend :8000]
      │
      ├──► [PostgreSQL :5432]  (SQLAlchemy ORM)
      │
      ├──► [Redis :6379]       (Task Queue)
      │         │
      │         ▼
      │    [Celery Worker]     (OR-Tools Solver)
      │         │
      │         ▼
      │    [PostgreSQL]        (Save results)
      │
      └──► [Ollama :11434]     (Local NLP Chat)
```

### 5. Key Design Decisions
1. **Synchronous Fallback**: The solver runs inline (not queued) when `SOLVER_ASYNC` is not set, avoiding dependency on a running Celery worker for local development.
2. **Auth Bypass**: Development mode bypasses JWT auth for faster iteration (`deps.py`).
3. **Sparse Variables**: The solver pre-filters invalid room-course pairs before creating decision variables, dramatically reducing the search space.
4. **Consecutive Block Logic**: Labs use a "temporal neighbor" constraint to enforce 2-hour blocks in the same room.
