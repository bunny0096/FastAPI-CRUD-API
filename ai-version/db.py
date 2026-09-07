import os
from typing import List, Optional, Dict, Any
import psycopg
from psycopg.rows import dict_row

DATABASE_URL = os.getenv("DATABASE_URL", "postgres://postgres:dev@localhost:5432/tasks")

SEED_TASKS = [
    {"title": "Learn HTTP basics", "done": True},
    {"title": "Build a CRUD API", "done": False},
    {"title": "Test endpoints in Swagger UI", "done": False},
]

def get_connection():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)

def init_db():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    done BOOLEAN NOT NULL DEFAULT FALSE
                );
            """)
            cur.execute("SELECT COUNT(*) AS count FROM tasks;")
            result = cur.fetchone()
            if result and result["count"] == 0:
                for task in SEED_TASKS:
                    cur.execute(
                        "INSERT INTO tasks (title, done) VALUES (%s, %s);",
                        (task["title"], task["done"]),
                    )
            conn.commit()

def get_tasks() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, title, done FROM tasks ORDER BY id;")
            return cur.fetchall()

def get_task(task_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, title, done FROM tasks WHERE id = %s;", (task_id,))
            return cur.fetchone()

def create_task(title: str, done: bool = False) -> Dict[str, Any]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING id, title, done;",
                (title, done),
            )
            created = cur.fetchone()
            conn.commit()
            return created

def update_task(task_id: int, title: str, done: bool) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE tasks SET title = %s, done = %s WHERE id = %s RETURNING id, title, done;",
                (title, done, task_id),
            )
            updated = cur.fetchone()
            conn.commit()
            return updated

def delete_task(task_id: int) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM tasks WHERE id = %s RETURNING id;", (task_id,))
            deleted = cur.fetchone()
            conn.commit()
            return deleted is not None
