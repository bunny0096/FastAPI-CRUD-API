from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

app = FastAPI(title="Task API", version="1.0")

tasks = [
    {"id": 1, "title": "Learn HTTP basics", "done": True},
    {"id": 2, "title": "Build a CRUD API", "done": False},
    {"id": 3, "title": "Test endpoints in Swagger UI", "done": False},
]


def find_task(task_id: int):
    return next((task for task in tasks if task["id"] == task_id), None)


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


@app.get("/", summary="Describe the API")
def root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health", summary="Check whether the API is running")
def health():
    return {"status": "ok"}


@app.get("/tasks", summary="List all tasks")
def list_tasks():
    return tasks


@app.get("/tasks/{task_id}", summary="Get one task by id")
def get_task(task_id: int):
    task = find_task(task_id)
    if task is None:
        return error_response(404, f"Task {task_id} not found")
    return task


@app.post("/tasks", status_code=201, summary="Create a task")
async def create_task(request: Request):
    body = await read_json_body(request)
    if body is None:
        return error_response(400, "Request body must be a JSON object")

    title = clean_title(body.get("title"))
    if title is None:
        return error_response(400, "Title is required and cannot be empty")

    next_id = max((task["id"] for task in tasks), default=0) + 1
    task = {"id": next_id, "title": title, "done": False}
    tasks.append(task)
    return task


@app.put("/tasks/{task_id}", summary="Update a task")
async def update_task(task_id: int, request: Request):
    task = find_task(task_id)
    if task is None:
        return error_response(404, f"Task {task_id} not found")

    body = await read_json_body(request)
    if body is None:
        return error_response(400, "Request body must be a JSON object")

    if "title" not in body and "done" not in body:
        return error_response(400, "Request body must include title or done")

    if "title" in body:
        title = clean_title(body.get("title"))
        if title is None:
            return error_response(400, "Title is required and cannot be empty")
        task["title"] = title

    if "done" in body:
        if not isinstance(body.get("done"), bool):
            return error_response(400, "Done must be true or false")
        task["done"] = body["done"]

    return task


@app.delete("/tasks/{task_id}", status_code=204, summary="Delete a task")
def delete_task(task_id: int):
    task = find_task(task_id)
    if task is None:
        return error_response(404, f"Task {task_id} not found")

    tasks.remove(task)
    return Response(status_code=204)
