import os
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

import db

app = FastAPI(
    title="Task API",
    version="1.0",
    description="A containerized PostgreSQL-backed CRUD API for managing to-do tasks.",
)


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


@app.on_event("startup")
def on_startup():
    db.init_db()


# Ensure db is initialized upon module load as well
db.init_db()


@app.get("/", summary="Describe the API", tags=["system"])
def root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health", summary="Check whether the API and database are running", tags=["system"])
def health():
    db_ok = db.check_db()
    if db_ok:
        return {"status": "ok", "db": "ok"}
    return JSONResponse(status_code=503, content={"status": "degraded", "db": "error"})


@app.get("/tasks", summary="List all tasks", tags=["tasks"])
def list_tasks():
    return db.get_all_tasks()


@app.get("/tasks/{task_id}", summary="Get one task by id", tags=["tasks"])
def get_task(task_id: int):
    task = db.get_task(task_id)
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

    created = db.create_task(title, done=False)
    return created


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
    task = db.get_task(task_id)
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

    updated = db.update_task(task_id, title=title, done=done)
    return updated


@app.delete(
    "/tasks/{task_id}", status_code=204, summary="Delete a task", tags=["tasks"]
)
def delete_task(task_id: int):
    task = db.get_task(task_id)
    if task is None:
        return error_response(404, f"Task {task_id} not found")

    db.delete_task(task_id)
    return Response(status_code=204)
