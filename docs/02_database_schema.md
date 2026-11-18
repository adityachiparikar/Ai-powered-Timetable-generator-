# Database Schema Design
## PostgreSQL Relational Schema

### 1. Core Entities

#### `users`
- `id`: UUID (PK)
- `email`: VARCHAR (Unique)
- `full_name`: VARCHAR
- `hashed_password`: VARCHAR
- `is_active`: BOOLEAN
- `is_superuser`: BOOLEAN
- `created_at`: TIMESTAMP
- `updated_at`: TIMESTAMP

#### `teachers`
- `id`: UUID (PK)
- `name`: VARCHAR
- `email`: VARCHAR
- `max_weekly_hours`: INTEGER
- `created_at`: TIMESTAMP
- `updated_at`: TIMESTAMP

**Related**: `teacher_constraints` (availability windows per day)

#### `student_groups` (Divisions)
- `id`: UUID (PK)
- `name`: VARCHAR (e.g., "TY-A", "SY-B", "SY-SEDA")
- `size`: INTEGER (e.g., 60)
- `year_level`: INTEGER
- `created_at`: TIMESTAMP
- `updated_at`: TIMESTAMP

#### `batches` (Lab Sub-Groups)
- `id`: UUID (PK)
- `name`: VARCHAR (e.g., "B1", "B2", "B3")
- `student_group_id`: UUID (FK → student_groups)
- `size`: INTEGER
- `created_at`: TIMESTAMP
- `updated_at`: TIMESTAMP

#### `courses`
- `id`: UUID (PK)
- `code`: VARCHAR (e.g., "ML101-A-T", "ML102-B-L-B1")
- `name`: VARCHAR (e.g., "DBMS", "DSA")
- `course_type`: ENUM (THEORY, LAB, TUTORIAL)
- `weekly_sessions`: INTEGER
- `teacher_id`: UUID (FK → teachers)
- `student_group_id`: UUID (FK → student_groups)
- `batch_id`: UUID (FK → batches, nullable for Theory)
- `created_at`: TIMESTAMP
- `updated_at`: TIMESTAMP

#### `rooms`
- `id`: UUID (PK)
- `name`: VARCHAR
- `capacity`: INTEGER
- `is_lab`: BOOLEAN
- `building`: VARCHAR
- `created_at`: TIMESTAMP
- `updated_at`: TIMESTAMP

#### `timeslots`
- `id`: UUID (PK)
- `day_of_week`: VARCHAR (Monday–Saturday)
- `start_time`: TIME
- `end_time`: TIME
- `is_break`: BOOLEAN
- `created_at`: TIMESTAMP
- `updated_at`: TIMESTAMP

### 2. Timetable Output

#### `timetable_entries`
- `id`: UUID (PK)
- `term`: VARCHAR (e.g., "Fall 2025")
- `course_id`: UUID (FK → courses)
- `course_code`: VARCHAR
- `teacher_id`: UUID (FK → teachers, nullable)
- `room_id`: UUID (FK → rooms)
- `room_name`: VARCHAR
- `batch_id`: UUID (FK → batches, nullable)
- `time_slot_id`: UUID (FK → timeslots)
- `student_group`: VARCHAR
- `day`: VARCHAR
- `time_range`: VARCHAR (e.g., "09:00 - 10:00")

### 3. AI & Logging

#### `constraintlogs`
- `id`: UUID (PK)
- `term`: VARCHAR
- `user_id`: VARCHAR
- `original_assignment`: JSON
- `new_assignment`: JSON
- `reason_category`: VARCHAR
- `reason_text`: VARCHAR
- `created_at`: TIMESTAMP
- `updated_at`: TIMESTAMP

#### `mlmodelartifacts`
- `id`: UUID (PK)
- `version`: VARCHAR
- `file_path`: VARCHAR
- `accuracy_score`: FLOAT
- `features_config`: JSON
- `is_active`: INTEGER
- `created_at`: TIMESTAMP
- `updated_at`: TIMESTAMP

### 4. Current Scale (Production Data)
| Table | Record Count |
|---|---|
| Teachers | 26 |
| Rooms | 9 |
| Student Groups | 11 |
| Courses | 220 (54 Theory + 120 Lab + 46 Tutorial) |
| Time Slots | 60 (Mon–Sat, 10 per day) |
| Timetable Entries | 387 |

### 5. Entity Relationships
```
teachers ──┐
            ├──► courses ◄── student_groups
batches ───┘                      │
                                  │
                            batches (children)

timeslots ─┐
rooms ─────┼──► timetable_entries ◄── courses
teachers ──┘
```
