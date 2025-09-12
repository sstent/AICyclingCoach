---

# **AI-Assisted Cycling Coach — Design Document**

## **1. Architecture Overview**

**Goal:** Web-based cycling coach that plans workouts, analyzes Garmin rides, and integrates AI while enforcing strict user-defined rules.

### **Components**

| Component        | Tech                       | Purpose                                                            |
| ---------------- | -------------------------- | ------------------------------------------------------------------ |
| Frontend         | React/Next.js              | UI for routes, plans, analysis, file uploads                       |
| Backend          | Python (FastAPI, async)    | API layer, AI integration, Garmin sync, DB access                  |
| Database         | PostgreSQL                 | Stores routes, sections, plans, rules, workouts, prompts, analyses |
| File Storage     | Mounted folder `/data/gpx` | Store GPX files for sections/routes                                |
| AI Integration   | OpenRouter via backend     | Plan generation, workout analysis, suggestions                     |
| Containerization | Docker + docker-compose    | Encapsulate frontend, backend, database with persistent storage    |

**Workflow Overview**

1. Upload/import GPX → backend saves to mounted folder + metadata in DB
2. Define plaintext rules → Store directly in DB
3. Generate plan → AI creates JSON plan → DB versioned
4. Ride recorded on Garmin → backend syncs activity metrics → stores in DB
5. AI analyzes workout → feedback & suggestions stored → user approves → new plan version created

---

## **2. Backend Design (Python, Async)**

**Framework:** FastAPI (async-first, non-blocking I/O)
**Tasks:**

* **Route/Section Management:** Upload GPX, store metadata, read GPX files for visualization
* **Rule Management:** CRUD rules with plaintext storage
* **Plan Management:** Generate plans (AI), store versions
* **Workout Analysis:** Fetch Garmin activity, run AI analysis, store reports
* **AI Integration:** Async calls to OpenRouter
* **Database Interaction:** Async Postgres client (e.g., `asyncpg` or `SQLAlchemy Async`)

**Endpoints (examples)**

| Method | Endpoint            | Description                                      |
| ------ | ------------------- | ------------------------------------------------ |
| POST   | `/routes/upload`    | Upload GPX file for route/section                |
| GET    | `/routes`           | List routes and sections                         |
| POST   | `/rules`            | Create new rule set (plaintext)                  |
| POST   | `/plans/generate`   | Generate new plan using rules & goals            |
| GET    | `/plans/{plan_id}`  | Fetch plan JSON & version info                   |
| POST   | `/workouts/analyze` | Trigger AI analysis for a synced Garmin activity |
| POST   | `/workouts/approve` | Approve AI suggestions → create new plan version |

**Async Patterns:**

* File I/O → async reading/writing GPX
* AI API calls → async HTTP requests
* Garmin sync → async polling/scheduled jobs

---

## **3. Database Design (Postgres)**

**Tables:**

```sql
-- Routes & Sections
CREATE TABLE routes (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE sections (
    id SERIAL PRIMARY KEY,
    route_id INT REFERENCES routes(id),
    gpx_file_path TEXT NOT NULL,
    distance_m NUMERIC,
    grade_avg NUMERIC,
    min_gear TEXT,
    est_time_minutes NUMERIC,
    created_at TIMESTAMP DEFAULT now()
);

-- Rules (plaintext storage)
CREATE TABLE rules (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    user_defined BOOLEAN DEFAULT true,
    rule_text TEXT NOT NULL, -- Plaintext rules
    version INT DEFAULT 1,
    parent_rule_id INT REFERENCES rules(id),
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

-- Plans (versioned)
CREATE TABLE plans (
    id SERIAL PRIMARY KEY,
    jsonb_plan JSONB NOT NULL,
    version INT NOT NULL,
    created_at TIMESTAMP DEFAULT now()
);

-- Workouts
CREATE TABLE workouts (
    id SERIAL PRIMARY KEY,
    plan_id INT REFERENCES plans(id),
    garmin_activity_id TEXT NOT NULL,
    metrics JSONB,
    created_at TIMESTAMP DEFAULT now()
);

-- Analyses
CREATE TABLE analyses (
    id SERIAL PRIMARY KEY,
    workout_id INT REFERENCES workouts(id),
    jsonb_feedback JSONB,
    created_at TIMESTAMP DEFAULT now()
);

-- AI Prompts
CREATE TABLE prompts (
    id SERIAL PRIMARY KEY,
    action_type TEXT, -- plan, analysis, suggestion
    model TEXT,
    prompt_text TEXT,
    version INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT now()
);
```

---

## **4. Containerization (Docker Compose)**

```yaml
version: '3.9'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - gpx-data:/app/data/gpx
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/cycling
    depends_on:
      - db

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"

  db:
    image: postgres:15
    restart: always
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
      POSTGRES_DB: cycling
    volumes:
      - postgres-data:/var/lib/postgresql/data

volumes:
  gpx-data:
    driver: local
  postgres-data:
    driver: local
```

**Notes:**

* `/app/data/gpx` inside backend container is persisted on host via `gpx-data` volume.
* Postgres data persisted via `postgres-data`.
* Backend talks to DB via async client.

---

## **5. Frontend UI Layouts & Flows**

### **5.1 Layout**

* **Navbar:** Routes | Rules | Plans | Workouts | Analysis | Export/Import
* **Sidebar:** Filters (date, type, difficulty)
* **Main Area:** Dynamic content depending on selection

### **5.2 Key Screens**

1. **Routes**

   * Upload/import GPX
   * View route map + section metadata
2. **Rules**

   * Plaintext rule editor
   * Simple create/edit form
   * Rule version history
3. **Plan**

   * Select goal + rule set → generate plan
   * View plan timeline & weekly workouts
4. **Workout Analysis**

   * List synced Garmin activities
   * Select activity → AI generates report
   * Visualizations: HR, cadence, power vs planned
   * Approve suggestions → new plan version
5. **Export/Import**

   * Export JSON/ZIP of routes, rules, plans
   * Import JSON/GPX

### **5.3 User Flow Example**

1. Upload GPX → backend saves file + DB metadata
2. Define rule set → Store plaintext → DB versioned
3. Generate plan → AI → store plan version in DB
4. Sync Garmin activity → backend fetches metrics → store workout
5. AI analyzes → report displayed → user approves → new plan version
6. Export plan or route as needed

---

## **6. AI Integration**

* Each **action type** (plan generation, analysis, suggestion) has:

  * Stored prompt template in DB
  * Configurable model per action
* Async calls to OpenRouter
* Store raw AI output + processed structured result in DB
* Use plaintext rules directly in prompts without parsing

---

## ✅ **Next Steps**

1. Implement **Python FastAPI backend** with async patterns.
2. Build **Postgres DB schema** and migration scripts.
3. Setup **Docker Compose** with mounted GPX folder.
4. Design frontend UI based on the flows above.
5. Integrate AI endpoints and Garmin sync.

---

