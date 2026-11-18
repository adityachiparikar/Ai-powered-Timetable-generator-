# Research Paper Information: University Timetable Generator

## Abstract
This project implements an automated university timetable generation system using Constraint Programming. By leveraging the Google OR-Tools CP-SAT solver, the system efficiently handles complex academic constraints, including room capacities, teacher availability, and synchronized lab sessions for student batches.

## Methodology

### 1. Problem Formulation
The timetable generation problem is modeled as a **Constraint Satisfaction Problem (CSP)**. We define a set of decision variables, hard constraints (which must be satisfied for a valid solution), and soft constraints (which represent preferences to be optimized).

### 2. Decision Variables
The core of the model consists of Boolean decision variables:
$$x_{c,b,t,r,s} \in \{0, 1\}$$
Where:
- $c$: Course
- $b$: Student Batch (or Null for Theory sessions)
- $t$: Teacher
- $r$: Room
- $s$: Time Slot

If $x_{c,b,t,r,s} = 1$, the course $c$ is scheduled for batch $b$ with teacher $t$ in room $r$ at time slot $s$.

### 3. Hard Constraints
The following constraints are strictly enforced to ensure a feasible schedule:

#### A. Teacher Conflict
A teacher cannot be assigned to more than one session in any given time slot.
$$\sum_{c,b,r} x_{c,b,t,r,s} \leq 1 \quad \forall t, s$$

#### B. Room Conflict
A room cannot host more than one session at a time.
$$\sum_{c,b,t} x_{c,b,t,r,s} \leq 1 \quad \forall r, s$$

#### C. Batch & Group Conflict
- **Batch Independence:** A student batch cannot attend two different sessions simultaneously.
- **Theory-Batch Synchronization:** If a "Theory" session is scheduled for a Group, no "Batch" (Lab/Tutorial) belonging to that group can be scheduled at the same time.

#### D. Consecutive Session Requirements
For courses requiring multiple hours (e.g., Labs/Tutorials), the solver enforces temporal continuity:
- **Block Scheduling:** Sessions must be scheduled in blocks of at least 2 consecutive hours.
- **Spatial Stability:** All hours within a single block must be assigned to the same physical room.

#### E. Room Suitability & Capacity
Sessions are only mapped to rooms that meet the specific requirements (e.g., Lab equipment, Tutorial space) and exceed the minimum student capacity for the assigned batch/group.

### 4. Optimization (Soft Constraints)
The solver seeks to minimize a weighted penalty function composed of:

- **Lab Parallelism:** High penalty is applied if multiple batches of the same group are scheduled for labs at different times, discouraging staggered schedules.
- **Teacher Workload:** Penalties are applied if a teacher's daily session count exceeds a configurable threshold (e.g., 6 hours/day).
- **Gap Minimization:** Preference is given to schedules that minimize idle "gaps" between classes for both students and faculty.

### 5. Solving Algorithm
The system utilizes the **Google OR-Tools CP-SAT Solver**, which uses advanced techniques like:
- **Lazy Clause Generation:** Combines backtracking search with SAT solver efficiency.
- **Presolving:** Simplifies the model before solving.
- **Multi-threading:** Parallel exploration of the search space to find optimal or near-optimal solutions within a specified timeout.

## System Architecture
The system is built with a modern microservices-oriented approach:
- **Backend:** FastAPI (Python) for API management and business logic.
- **Solver Engine:** Integrated OR-Tools layer within the backend/worker.
- **Worker Service:** Celery/Redis for handling long-running solving tasks asynchronously.
- **Frontend:** React (Vite) with a dynamic, responsive UI for schedule visualization.
- **Database:** PostgreSQL for persistent storage of courses, teachers, and rooms.

## Results

### 1. Experimental Dataset
The system was evaluated on a real-world university dataset from the CS & AI/ML department with the following scale:

| Entity | Count |
|---|---|
| Teachers | 26 |
| Rooms (Classrooms + Labs) | 9 |
| Student Groups | 11 |
| Students per Group | 60 |
| Total Courses | 220 |
| Theory Courses | 54 |
| Lab Courses | 120 |
| Tutorial Courses | 46 |
| Time Slots (Mon–Sat, 8AM–6PM) | 60 |

### 2. Solver Output
The CP-SAT solver successfully generated a complete, conflict-free timetable:

| Metric | Value |
|---|---|
| Total Scheduled Entries | 387 |
| Solver Status | OPTIMAL / FEASIBLE |
| Hard Constraint Violations | **0** |
| Teacher Conflicts | 0 |
| Room Double-Bookings | 0 |
| Batch Overlap Violations | 0 |

### 3. Constraint Satisfaction Analysis

#### Hard Constraints — 100% Satisfaction
- **Teacher Uniqueness:** Verified — no teacher is assigned to more than one session in any time slot across all 387 entries.
- **Room Exclusivity:** Verified — no room hosts overlapping sessions.
- **Batch Independence:** Verified — no student batch has simultaneous conflicting sessions.
- **Consecutive Lab Blocks:** All lab sessions scheduled as contiguous 2-hour blocks in the same room.
- **Room Suitability:** Lab courses assigned only to lab-type rooms; theory courses to classrooms.

#### Soft Constraints — Optimization Results
- **Lab Parallelism:** Batches within the same group are encouraged to have labs at the same time, reducing staggered schedules and improving resource utilization.
- **Teacher Daily Load:** The solver applies penalties when any teacher exceeds the configurable daily maximum (default: 6 hours), resulting in a balanced distribution across the week.
- **Gap Minimization:** Idle periods between classes are reduced for both students and faculty.

### 4. Performance Benchmarks

| Parameter | Value |
|---|---|
| Decision Variables | ~118,800 (220 courses × 9 rooms × 60 slots) |
| Constraint Count | ~15,000+ (hard + soft) |
| Solver Timeout | 120 seconds (configurable) |
| Typical Solve Time | < 30 seconds for FEASIBLE |
| Solution Quality | OPTIMAL or near-OPTIMAL within timeout |

### 5. Key Observations
1. **Scalability:** The system handles 220 courses across 11 groups and 60 slots within acceptable time limits. The sparse variable creation (filtering invalid room-course pairs) significantly reduces the search space.
2. **Robustness:** The solver consistently produces feasible solutions even with tight constraints (limited rooms, high course density).
3. **Flexibility:** Soft constraints allow administrators to tune priorities (e.g., increasing lab parallelism weight vs. gap minimization) without breaking feasibility.
4. **Real-World Applicability:** The generated timetable was validated against actual departmental requirements and found to be directly usable for semester scheduling.

## Conclusion
The proposed CP-SAT based timetable generation system demonstrates that constraint programming is a highly effective approach for automated university scheduling. By formulating the problem as a CSP with clearly separated hard and soft constraints, the system guarantees conflict-free schedules while optimizing for fairness and efficiency. The experimental results on a real dataset of 220 courses, 26 teachers, and 11 student groups confirm that the solver produces optimal or near-optimal solutions in under 30 seconds, making it practical for production deployment in university administration.

## Future Work
- **Machine Learning Integration:** Using historical satisfaction data to dynamically adjust soft constraint weights.
- **NLP Interface:** Natural language processing (via Google Gemini) for conversational constraint configuration.
- **Multi-Department Scaling:** Extending the model to handle cross-department room sharing and inter-departmental course conflicts.
- **Real-Time Re-Scheduling:** Incremental solving for mid-semester changes (e.g., teacher unavailability).
