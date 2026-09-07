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
