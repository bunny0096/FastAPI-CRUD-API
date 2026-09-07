import os
import sys
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
import psycopg
from psycopg.rows import dict_row

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgres://postgres:dev@localhost:5432/tasks")

SEED_TASKS = [
    {"title": "Learn HTTP basics", "done": True},
    {"title": "Build a CRUD API", "done": False},
    {"title": "Test endpoints in Swagger UI", "done": False},
]


def get_db_connection():
    """Establish and return a new connection to the PostgreSQL database."""
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def init_db():
    """Create the tasks table if missing and seed initial tasks if empty."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    done BOOLEAN NOT NULL DEFAULT FALSE
                );
                """
            )
            cur.execute("SELECT COUNT(*) AS count FROM tasks;")
            row = cur.fetchone()
            count = row["count"] if row else 0

            if count == 0:
                for task in SEED_TASKS:
                    cur.execute(
                        "INSERT INTO tasks (title, done) VALUES (%s, %s);",
                        (task["title"], task["done"]),
                    )
            conn.commit()


def get_all_tasks() -> List[Dict[str, Any]]:
    """Retrieve all tasks from the database ordered by id."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, title, done FROM tasks ORDER BY id;")
            rows = cur.fetchall()
            return [dict(row) for row in rows]


def get_task(task_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a single task by its id."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, title, done FROM tasks WHERE id = %s;",
                (task_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None


def create_task(title: str, done: bool = False) -> Dict[str, Any]:
    """Insert a new task and return the created record."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING id, title, done;",
                (title, done),
            )
            created_task = cur.fetchone()
            conn.commit()
            return dict(created_task)


def update_task(task_id: int, title: str, done: bool) -> Optional[Dict[str, Any]]:
    """Update title and done state for an existing task."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE tasks SET title = %s, done = %s WHERE id = %s RETURNING id, title, done;",
                (title, done, task_id),
            )
            updated_task = cur.fetchone()
            conn.commit()
            return dict(updated_task) if updated_task else None


def delete_task(task_id: int) -> bool:
    """Delete a task by its id. Returns True if a row was deleted, False otherwise."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM tasks WHERE id = %s RETURNING id;", (task_id,))
            deleted_row = cur.fetchone()
            conn.commit()
            return deleted_row is not None


def check_db() -> bool:
    """Ping the database by executing SELECT 1."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                return True
    except Exception:
        return False
