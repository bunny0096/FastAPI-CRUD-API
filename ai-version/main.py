from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List
import db

app = FastAPI(title="Task API (AI Version)")

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1)

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None

@app.on_event("startup")
def startup():
    db.init_db()

@app.get("/tasks")
def list_tasks():
    return db.get_tasks()

@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate):
    title = payload.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="Title is required and cannot be empty")
    return db.create_task(title, done=False)

@app.put("/tasks/{task_id}")
def update_task(task_id: int, payload: TaskUpdate):
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if payload.title is None and payload.done is None:
        raise HTTPException(status_code=400, detail="Request body must include title or done")
    
    title = payload.title.strip() if payload.title is not None else task["title"]
    if payload.title is not None and not title:
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    
    done = payload.done if payload.done is not None else task["done"]
    return db.update_task(task_id, title=title, done=done)

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int):
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete_task(task_id)
    return None
