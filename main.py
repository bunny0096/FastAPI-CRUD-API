from fastapi import FastAPI
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
