# Task API

A small FastAPI CRUD API for managing an in-memory to-do list. It supports creating, reading, updating, and deleting tasks, and includes Swagger UI at `/docs`.

## Install

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

## Run

```bash
.venv/bin/uvicorn main:app --reload
```

The API runs at `http://127.0.0.1:8000`.

## Endpoints

| Method | Path | Description | Success |
| --- | --- | --- | --- |
| GET | `/` | API name, version, and endpoint list | `200 OK` |
| GET | `/health` | Server health check | `200 OK` |
| GET | `/tasks` | List all tasks | `200 OK` |
| GET | `/tasks/{task_id}` | Get one task by id | `200 OK` |
| POST | `/tasks` | Create a task with `{"title": "Buy milk"}` | `201 Created` |
| PUT | `/tasks/{task_id}` | Update a task title and/or done state | `200 OK` |
| DELETE | `/tasks/{task_id}` | Delete a task | `204 No Content` |

Errors use JSON, for example `{"error": "Task 99 not found"}`. Invalid request bodies return `400 Bad Request`; unknown task ids return `404 Not Found`.

## Example curl output

```bash
curl -i -X POST http://127.0.0.1:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Buy milk"}'
```

```text
HTTP/1.1 201 Created
date: Mon, 31 Aug 2026 11:05:31 GMT
server: uvicorn
content-length: 40
content-type: application/json

{"id":4,"title":"Buy milk","done":false}
```

## Swagger UI

Open `http://127.0.0.1:8000/docs` after starting the server.

![Swagger UI showing Task API endpoints](docs/swagger-ui.png)

## Notes

Tasks are stored in memory, so any tasks created after startup disappear when the server restarts. A database would be needed to keep data permanently.

## Publish to GitHub

After creating a public GitHub repository, connect and push this local repo:

```bash
git remote add origin <your-github-repo-url>
git push -u origin main
```
