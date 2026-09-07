# Task API: Containerized FastAPI + PostgreSQL Stack

A production-grade, containerized CRUD API for managing tasks, powered by **FastAPI**, **psycopg 3**, and **PostgreSQL 16**, fully orchestrated with **Docker Compose**.

---

## The One Command to Run Everything

From a fresh clone, spin up both the database and the API container with a single command:

```bash
cp .env.example .env && docker compose up --build
```

The API will be live at `http://localhost:3000` (and Swagger documentation at `http://localhost:3000/docs`).

To run in the background (detached):
```bash
docker compose up -d
```

To stop the stack:
```bash
docker compose down
```

---

## Architecture & Configuration

The application consists of two isolated Docker services connected via an internal bridge network:
1. **`db`**: Official `postgres:16-alpine` image with data mounted onto named volume `taskdata`. Includes a Docker healthcheck using `pg_isready`.
2. **`api`**: Python 3.12 slim container running FastAPI via Uvicorn on port `3000`. Starts only when `db` is healthy (`condition: service_healthy`).

### Environment Variables

Configuration and database secrets are loaded from `.env` (which is git-ignored). See `.env.example` for reference:

```bash
# .env.example
DATABASE_URL=postgres://postgres:dev@localhost:5432/tasks
PORT=3000
```

Inside Docker Compose, the connection string dynamically routes to the database service name `db`:
```bash
DATABASE_URL=postgres://postgres:dev@db:5432/tasks
```

No passwords or database secrets are hardcoded in application source files or git history.

---

## Endpoints

| Method | Path | Description | Success Status | Error Statuses |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/` | API name, version, and endpoints list | `200 OK` | - |
| `GET` | `/health` | Live DB ping (`SELECT 1`) | `200 OK` | `503 Service Unavailable` |
| `GET` | `/tasks` | List all tasks ordered by `id` | `200 OK` | - |
| `GET` | `/tasks/{id}` | Retrieve a single task by ID | `200 OK` | `404 Not Found` |
| `POST` | `/tasks` | Create a task (`{"title": "..."}`) | `201 Created` | `400 Bad Request` |
| `PUT` | `/tasks/{id}` | Update title and/or done status | `200 OK` | `400 Bad Request`, `404 Not Found` |
| `DELETE` | `/tasks/{id}` | Delete a task by ID | `204 No Content` | `404 Not Found` |

---

## Verified `curl -i` Output

### 1. Health Check (`GET /health`)
```bash
curl -i http://localhost:3000/health
```
```http
HTTP/1.1 200 OK
date: Mon, 07 Sep 2026 10:06:54 GMT
server: uvicorn
content-length: 25
content-type: application/json

{"status":"ok","db":"ok"}
```

### 2. List Tasks (`GET /tasks`)
```bash
curl -i http://localhost:3000/tasks
```
```http
HTTP/1.1 200 OK
date: Mon, 07 Sep 2026 10:07:00 GMT
server: uvicorn
content-length: 226
content-type: application/json

[
  {"id":1,"title":"Learn HTTP basics","done":true},
  {"id":2,"title":"Build a CRUD API","done":false},
  {"id":3,"title":"Test endpoints in Swagger UI","done":false},
  {"id":4,"title":"Verify Docker Compose persistence","done":false}
]
```

### 3. Create Task (`POST /tasks`)
```bash
curl -i -X POST http://localhost:3000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Deploy stack with Docker Compose"}'
```
```http
HTTP/1.1 201 Created
date: Mon, 07 Sep 2026 10:10:53 GMT
server: uvicorn
content-length: 64
content-type: application/json

{"id":5,"title":"Deploy stack with Docker Compose","done":false}
```

### 4. Update Task (`PUT /tasks/5`)
```bash
curl -i -X PUT http://localhost:3000/tasks/5 \
  -H "Content-Type: application/json" \
  -d '{"title": "Deploy stack with Docker Compose", "done": true}'
```
```http
HTTP/1.1 200 OK
date: Mon, 07 Sep 2026 10:11:03 GMT
server: uvicorn
content-length: 63
content-type: application/json

{"id":5,"title":"Deploy stack with Docker Compose","done":true}
```

### 5. Delete Task (`DELETE /tasks/5`)
```bash
curl -i -X DELETE http://localhost:3000/tasks/5
```
```http
HTTP/1.1 204 No Content
date: Mon, 07 Sep 2026 10:11:14 GMT
server: uvicorn
```

### 6. Not Found Error Handling (`GET /tasks/999`)
```bash
curl -i http://localhost:3000/tasks/999
```
```http
HTTP/1.1 404 Not Found
date: Mon, 07 Sep 2026 10:11:22 GMT
server: uvicorn
content-length: 30
content-type: application/json

{"error":"Task 999 not found"}
```

### 7. Bad Request Validation (`POST /tasks` with empty title)
```bash
curl -i -X POST http://localhost:3000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": ""}'
```
```http
HTTP/1.1 400 Bad Request
date: Mon, 07 Sep 2026 10:11:28 GMT
server: uvicorn
content-length: 49
content-type: application/json

{"error":"Title is required and cannot be empty"}
```

---

## Database Verification & Screenshot

Inside the containerized Postgres database, verify the schema and stored records using `psql`:

```bash
docker exec -it containerizethestack-db-1 psql -U postgres -d tasks -c "\dt" -c "SELECT * FROM tasks;"
```

![PostgreSQL Database Screenshot in Docker](docs/db-screenshot.png)

---

## Data Persistence Across Full Restarts

All database records are stored on the Docker named volume `taskdata` (mapped to `/var/lib/postgresql/data`).
Even when containers are completely stopped and removed via `docker compose down`, rebuilding and restarting via `docker compose up` retains all existing records:

```bash
docker compose down
docker compose up -d
curl http://localhost:3000/tasks
# -> All existing tasks survive intact!
```

---

## Optional Extras & Deep Dive

### 1. The Mortality Experiment: Why Volumes Exist
A container's default writable layer is ephemeral. If you launch Postgres without a volume (`-v taskdata:...`), any rows created live purely in the container layer. When that container is removed (`docker rm`), its storage is immediately deallocated and the data is lost forever. A Docker volume separates lifecycle of state from the lifecycle of compute, ensuring rows survive container upgrades, restarts, and redeployments.

### 2. Production Health Check (`GET /health`)
The `/health` endpoint executes an active `SELECT 1` ping against PostgreSQL. In production, load balancers (such as AWS ALB or Nginx) use this endpoint to gate traffic: if PostgreSQL becomes unreachable or the connection pool saturates, `/health` returns `503 Service Unavailable`, prompting the load balancer to route requests away from unhealthy instances or trigger automatic container restarts.

### 3. Storage Abstraction ("Prove the Swap")
Throughout assignments A1, A2, and A3, the task API swapped storage engines three times:
1. In-memory list (A1)
2. SQLite single file (A2)
3. PostgreSQL container (A3)

Because all database interactions are encapsulated inside the repository module (`db.py`), route handlers in `main.py` and the external HTTP API contracts remain completely unchanged. This demonstrates that database engines are merely implementation details decoupled from API business logic.

---

## Stage 6: AI vs Me (Bonus Rematch)

### 1. The Specification Prompt
The prompt written from memory without referencing the assignment text:

> *"Write a production-ready Python FastAPI CRUD application for managing to-do tasks backed by PostgreSQL and containerized with Docker Compose.*
>
> *Requirements:*
> *1. Tech Stack: Python 3.12, FastAPI, Uvicorn, and raw PostgreSQL driver `psycopg` (v3). Do not use an ORM.*
> *2. Database Schema: A `tasks` table with columns `id SERIAL PRIMARY KEY`, `title TEXT NOT NULL`, and `done BOOLEAN NOT NULL DEFAULT FALSE`.*
> *3. Startup & Seeding: On application startup, connect to Postgres using `DATABASE_URL` from the environment, create the `tasks` table if it doesn't exist, and seed 3 initial sample tasks only if the table is empty (never re-seed on subsequent restarts).*
> *4. Endpoints: Implement 5 CRUD endpoints matching REST standards:*
> *   - `GET /tasks` (list all tasks ordered by id)*
> *   - `GET /tasks/{id}` (return 404 if not found with JSON error `{"error": "Task not found"}`)*
> *   - `POST /tasks` (validate title is present and non-empty, return 400 if invalid with JSON error; on success return 201 with created task)*
> *   - `PUT /tasks/{id}` (update title/done, return 404 if not found, return updated task)*
> *   - `DELETE /tasks/{id}` (delete task, return 404 if not found, return 204 with empty body on success)*
> *5. Security: Use parameterized queries (`%s` placeholders) everywhere to prevent SQL injection.*
> *6. Environment & Secrets: Read database credentials from environment variable `DATABASE_URL`. Never hardcode secrets. Provide a `.env.example`.*
> *7. Docker & Compose: Provide a Dockerfile and a `compose.yaml` containing two services: `api` and `db` (using `postgres:16-alpine`). The compose file must mount a named volume so data persists across restarts, and the api must be reachable on port 3000."*

The generated output was quarantined in `ai-version/`.

### 2. Concrete Differences Found (`git diff --no-index`)

1. **Startup Synchronization & Race Conditions (`compose.yaml`)**:
   - **Hand-built**: Implemented a Postgres health check (`test: ["CMD-SHELL", "pg_isready -U postgres -d tasks"]`) and configured `depends_on: db: condition: service_healthy`. The API container waits until Postgres is completely ready to accept socket connections.
   - **AI version**: Used bare `depends_on: - db`. In Docker Compose, this only waits for the container process to spawn. The API attempted connection immediately before the Postgres daemon finished initialization, throwing a connection refused exception on first boot.
2. **Resilience & Retry Logic (`db.py`)**:
   - **Hand-built**: Added an initialization retry loop (`init_db(max_retries=5, retry_delay=1.0)`) and an active DB ping function (`check_db()`).
   - **AI version**: Attempted connection once without retries or error handling.
3. **Error Response Schema & HTTP Status Contracts (`main.py`)**:
   - **Hand-built**: Enforced strict `{"error": "<message>"}` payloads with HTTP `400` status codes for validation failures and custom 404 responses matching the previous A1/A2 contracts.
   - **AI version**: Used FastAPI `HTTPException`, which defaults to `{"detail": "<message>"}` instead of `{"error": ...}`, and Pydantic validation schemas which return HTTP `422 Unprocessable Entity` instead of HTTP `400 Bad Request`.
4. **Image Footprint (`compose.yaml`)**:
   - **Hand-built**: Used `postgres:16-alpine` (~100 MB footprint).
   - **AI version**: Used standard Debian-based `postgres:16` (~400 MB footprint), needlessly ballooning image size and pull times.

### 3. What the AI Got Right vs Wrong
- **What it did well**: The AI correctly captured parameterized SQL queries (`%s`), wrote a clean multi-stage `.dockerignore`, avoided hardcoding passwords, and correctly named the Docker volume for persistent storage.
- **What it got wrong**: It failed to handle startup synchronization via healthchecks, used default Pydantic exceptions that altered API error contracts (producing `422` with `{"detail": ...}` instead of `400` with `{"error": ...}`), and lacked connection retry logic.
- **What the prompt forgot to specify**: The prompt should have explicitly instructed: *"Do not use Pydantic models for request validation if it results in HTTP 422; return HTTP 400 with a JSON key named 'error'. Additionally, configure a healthcheck on the database service in Docker Compose."*

### 4. Rematch Reflection
*Improved prompt specification:* Added explicit constraints regarding HTTP error codes (enforcing 400 over 422), the exact error JSON key structure (`error` vs `detail`), and Compose `service_healthy` conditions. With these constraints added, the AI regenerated code that closely matched the production architecture. The key lesson: an AI's code is only as robust as the reviewer's understanding of edge cases and systems engineering.
