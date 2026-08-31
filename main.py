import sqlite3
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

app = FastAPI(
    title="Task API",
    version="1.0",
    description="A small SQLite-backed CRUD API for managing to-do tasks.",
)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "tasks.db"

SEED_TASKS = [
    {"title": "Learn HTTP basics", "done": True},
    {"title": "Build a CRUD API", "done": False},
    {"title": "Test endpoints in Swagger UI", "done": False},
]


def get_db_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def row_to_task(row: sqlite3.Row | None):
    if row is None:
        return None

    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}


def init_db():
    with get_db_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0 CHECK (done IN (0, 1))
            )
            """
        )
        task_count = connection.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        if task_count == 0:
            connection.executemany(
                "INSERT INTO tasks (title, done) VALUES (?, ?)",
                [(task["title"], int(task["done"])) for task in SEED_TASKS],
            )
        connection.commit()


def find_task(task_id: int):
    with get_db_connection() as connection:
        row = connection.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
    return row_to_task(row)


def error_response(status_code: int, message: str):
    return JSONResponse(status_code=status_code, content={"error": message})


async def read_json_body(request: Request):
    try:
        body = await request.json()
    except ValueError:
        return None
    return body if isinstance(body, dict) else None


def clean_title(value: Any):
    if not isinstance(value, str):
        return None

    title = value.strip()
    return title or None


init_db()


@app.get("/", summary="Describe the API", tags=["system"])
def root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health", summary="Check whether the API is running", tags=["system"])
def health():
    return {"status": "ok"}


@app.get("/tasks", summary="List all tasks", tags=["tasks"])
def list_tasks():
    with get_db_connection() as connection:
        rows = connection.execute(
            "SELECT id, title, done FROM tasks ORDER BY id"
        ).fetchall()
    return [row_to_task(row) for row in rows]


@app.get("/tasks/{task_id}", summary="Get one task by id", tags=["tasks"])
def get_task(task_id: int):
    task = find_task(task_id)
    if task is None:
        return error_response(404, f"Task {task_id} not found")
    return task


@app.post(
    "/tasks",
    status_code=201,
    summary="Create a task",
    tags=["tasks"],
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "required": ["title"],
                        "properties": {"title": {"type": "string"}},
                    },
                    "example": {"title": "Buy milk"},
                }
            },
        }
    },
)
async def create_task(request: Request):
    body = await read_json_body(request)
    if body is None:
        return error_response(400, "Request body must be a JSON object")

    title = clean_title(body.get("title"))
    if title is None:
        return error_response(400, "Title is required and cannot be empty")

    with get_db_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO tasks (title, done) VALUES (?, ?)", (title, 0)
        )
        connection.commit()
        task_id = cursor.lastrowid

    return find_task(task_id)


@app.put(
    "/tasks/{task_id}",
    summary="Update a task",
    tags=["tasks"],
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "done": {"type": "boolean"},
                        },
                    },
                    "example": {"title": "Buy milk", "done": True},
                }
            },
        }
    },
)
async def update_task(task_id: int, request: Request):
    task = find_task(task_id)
    if task is None:
        return error_response(404, f"Task {task_id} not found")

    body = await read_json_body(request)
    if body is None:
        return error_response(400, "Request body must be a JSON object")

    if "title" not in body and "done" not in body:
        return error_response(400, "Request body must include title or done")

    title = task["title"]
    done = task["done"]

    if "title" in body:
        title = clean_title(body.get("title"))
        if title is None:
            return error_response(400, "Title is required and cannot be empty")

    if "done" in body:
        if not isinstance(body.get("done"), bool):
            return error_response(400, "Done must be true or false")
        done = body["done"]

    with get_db_connection() as connection:
        connection.execute(
            "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
            (title, int(done), task_id),
        )
        connection.commit()

    return find_task(task_id)


@app.delete(
    "/tasks/{task_id}", status_code=204, summary="Delete a task", tags=["tasks"]
)
def delete_task(task_id: int):
    task = find_task(task_id)
    if task is None:
        return error_response(404, f"Task {task_id} not found")

    with get_db_connection() as connection:
        connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        connection.commit()

    return Response(status_code=204)
