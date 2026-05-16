from __future__ import annotations

import sqlite3

from july.storage.utils import utc_now

IMPROVEMENT_STATUSES = {"open", "planned", "in_progress", "done", "dismissed"}
IMPROVEMENT_PRIORITIES = {"low", "normal", "high"}
TASK_STATUSES = {"pending", "in_progress", "done"}


class TaskRepository:
    def __init__(self, connection_factory):
        self.connection = connection_factory

    def create_project_improvement(
        self,
        project_key: str,
        title: str,
        *,
        description: str | None = None,
        status: str = "open",
        priority: str = "normal",
        source_channel: str = "cli",
        source_ref: str | None = None,
    ) -> dict:
        if status not in IMPROVEMENT_STATUSES:
            raise ValueError("Improvement status must be open, planned, in_progress, done, or dismissed")
        if priority not in IMPROVEMENT_PRIORITIES:
            raise ValueError("Improvement priority must be low, normal, or high")

        timestamp = utc_now()
        closed_at = timestamp if status in {"done", "dismissed"} else None
        with self.connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO project_improvements (
                    project_key, title, description, status, priority, source_channel, source_ref,
                    created_at, updated_at, closed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_key,
                    title,
                    description,
                    status,
                    priority,
                    source_channel,
                    source_ref,
                    timestamp,
                    timestamp,
                    closed_at,
                ),
            )
            row = conn.execute(
                "SELECT * FROM project_improvements WHERE id = ?",
                (cursor.lastrowid,),
            ).fetchone()
        return dict(row) if row is not None else {}

    def list_project_improvements(
        self,
        project_key: str,
        *,
        status: str | None = None,
        include_closed: bool = False,
        limit: int = 20,
    ) -> list[sqlite3.Row]:
        params: list[object] = [project_key]
        query = """
            SELECT id, project_key, title, description, status, priority, source_channel,
                   source_ref, created_at, updated_at, closed_at
            FROM project_improvements
            WHERE project_key = ?
        """
        if status:
            if status not in IMPROVEMENT_STATUSES:
                raise ValueError("Improvement status must be open, planned, in_progress, done, or dismissed")
            query += " AND status = ?"
            params.append(status)
        elif not include_closed:
            query += " AND status IN ('open', 'planned', 'in_progress')"
        query += """
            ORDER BY
                CASE priority
                    WHEN 'high' THEN 0
                    WHEN 'normal' THEN 1
                    ELSE 2
                END,
                id DESC
            LIMIT ?
        """
        params.append(limit)
        with self.connection() as conn:
            return conn.execute(query, tuple(params)).fetchall()

    def update_project_improvement_status(
        self,
        improvement_id: int,
        status: str,
        *,
        project_key: str | None = None,
    ) -> dict:
        if status not in IMPROVEMENT_STATUSES:
            raise ValueError("Improvement status must be open, planned, in_progress, done, or dismissed")

        timestamp = utc_now()
        closed_at = timestamp if status in {"done", "dismissed"} else None
        with self.connection() as conn:
            row = conn.execute(
                "SELECT * FROM project_improvements WHERE id = ?",
                (improvement_id,),
            ).fetchone()
            if row is None:
                raise ValueError(f"Improvement {improvement_id} not found")
            if project_key and row["project_key"] != project_key:
                raise ValueError(f"Improvement {improvement_id} does not belong to project {project_key}")

            conn.execute(
                """
                UPDATE project_improvements
                SET status = ?, updated_at = ?, closed_at = ?
                WHERE id = ?
                """,
                (status, timestamp, closed_at, improvement_id),
            )
            updated = conn.execute(
                "SELECT * FROM project_improvements WHERE id = ?",
                (improvement_id,),
            ).fetchone()
        return dict(updated) if updated is not None else {}

    def create_manual_task(
        self,
        project_key: str,
        title: str,
        *,
        details: str | None = None,
        status: str = "pending",
    ) -> dict:
        if status not in TASK_STATUSES:
            raise ValueError("Manual task status must be pending, in_progress, or done")

        timestamp = utc_now()
        with self.connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO tasks (
                    inbox_item_id, task_type, status, title, details, project_key, due_hint,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    None,
                    "manual_follow_up",
                    status,
                    title,
                    details,
                    project_key,
                    None,
                    timestamp,
                    timestamp,
                ),
            )
            row = conn.execute(
                "SELECT * FROM tasks WHERE id = ?",
                (cursor.lastrowid,),
            ).fetchone()
        return dict(row) if row is not None else {}

    def list_project_tasks(
        self,
        project_key: str,
        *,
        status: str | None = None,
        include_done: bool = False,
        limit: int = 20,
    ) -> list[sqlite3.Row]:
        params: list[object] = [project_key]
        query = """
            SELECT id, inbox_item_id, task_type, status, title, details, project_key,
                   due_hint, created_at, updated_at
            FROM tasks
            WHERE project_key = ?
        """
        if status:
            if status not in TASK_STATUSES:
                raise ValueError("Task status must be pending, in_progress, or done")
            query += " AND status = ?"
            params.append(status)
        elif not include_done:
            query += " AND status != 'done'"
        query += """
            ORDER BY
                CASE status
                    WHEN 'in_progress' THEN 0
                    WHEN 'pending' THEN 1
                    ELSE 2
                END,
                id DESC
            LIMIT ?
        """
        params.append(limit)
        with self.connection() as conn:
            return conn.execute(query, tuple(params)).fetchall()

    def update_task_status(
        self,
        task_id: int,
        status: str,
        *,
        project_key: str | None = None,
    ) -> dict:
        if status not in TASK_STATUSES:
            raise ValueError("Task status must be pending, in_progress, or done")

        timestamp = utc_now()
        with self.connection() as conn:
            row = conn.execute(
                "SELECT * FROM tasks WHERE id = ?",
                (task_id,),
            ).fetchone()
            if row is None:
                raise ValueError(f"Task {task_id} not found")
            if project_key and row["project_key"] != project_key:
                raise ValueError(f"Task {task_id} does not belong to project {project_key}")

            conn.execute(
                "UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?",
                (status, timestamp, task_id),
            )
            updated = conn.execute(
                "SELECT * FROM tasks WHERE id = ?",
                (task_id,),
            ).fetchone()
        return dict(updated) if updated is not None else {}
