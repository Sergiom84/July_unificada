from __future__ import annotations

import sqlite3


class MemoryRepository:
    def __init__(self, connection_factory):
        self.connection = connection_factory

    def list_inbox(self, limit: int = 20) -> list[sqlite3.Row]:
        with self.connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, detected_intent, status, domain, project_key, normalized_summary, created_at
                FROM inbox_items
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            )
            return cursor.fetchall()

    def list_tasks(self, status: str | None = None, limit: int = 20) -> list[sqlite3.Row]:
        query = """
            SELECT id, inbox_item_id, task_type, status, project_key, title, created_at
            FROM tasks
        """
        params: list[object] = []
        if status:
            query += " WHERE status = ?"
            params.append(status)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        with self.connection() as conn:
            cursor = conn.execute(query, tuple(params))
            return cursor.fetchall()

    def list_memory(self, limit: int = 20) -> list[sqlite3.Row]:
        with self.connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, inbox_item_id, memory_kind, status, domain, scope, project_key, title, created_at
                FROM memory_items
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            )
            return cursor.fetchall()

    def get_record(self, table: str, record_id: int) -> sqlite3.Row | None:
        allowed_tables = {
            "inbox_items", "tasks", "memory_items", "artifacts", "project_links",
            "clarification_events", "sessions", "topic_keys", "topic_links",
            "model_contributions", "url_metadata", "external_references", "projects",
            "project_improvements", "skill_references",
        }
        if table not in allowed_tables:
            raise ValueError(f"Unsupported table: {table}")
        with self.connection() as conn:
            cursor = conn.execute(f"SELECT * FROM {table} WHERE id = ?", (record_id,))
            return cursor.fetchone()
