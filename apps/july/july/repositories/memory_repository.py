from __future__ import annotations

import sqlite3

from july.storage.utils import utc_now


class MemoryRepository:
    def __init__(self, connection_factory):
        self.connection = connection_factory

    def capture(self, raw_input: str, source_channel: str, source_ref: str | None, plan: dict) -> dict:
        timestamp = utc_now()
        classification = plan["classification"]

        with self.connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO inbox_items (
                    raw_input, source_channel, source_ref, detected_intent, intent_confidence,
                    status, clarification_question, normalized_summary, domain, project_key,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    raw_input,
                    source_channel,
                    source_ref,
                    classification["intent"],
                    classification["confidence"],
                    classification["status"],
                    classification["clarification_question"],
                    classification["normalized_summary"],
                    classification["domain"],
                    classification["project_key"],
                    timestamp,
                    timestamp,
                ),
            )
            inbox_item_id = cursor.lastrowid

            task_id = self._insert_task(conn, inbox_item_id, plan["task"], timestamp)
            memory_item_id = self._insert_memory(conn, inbox_item_id, plan["memory"], timestamp)
            self._insert_artifacts(conn, inbox_item_id, plan["artifacts"], timestamp)
            self._insert_project_links(conn, inbox_item_id, memory_item_id, plan, timestamp)

        return {
            "inbox_item_id": inbox_item_id,
            "task_id": task_id,
            "memory_item_id": memory_item_id,
        }

    def resolve_clarification(self, inbox_item_id: int, answer: str, plan: dict) -> dict:
        timestamp = utc_now()
        classification = plan["classification"]

        with self.connection() as conn:
            inbox_item = conn.execute(
                "SELECT * FROM inbox_items WHERE id = ?",
                (inbox_item_id,),
            ).fetchone()
            if inbox_item is None:
                raise ValueError(f"Inbox item {inbox_item_id} not found")

            conn.execute(
                """
                INSERT INTO clarification_events (inbox_item_id, question, answer, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    inbox_item_id,
                    inbox_item["clarification_question"],
                    answer,
                    timestamp,
                ),
            )

            self._delete_derived_records(conn, inbox_item_id)

            conn.execute(
                """
                UPDATE inbox_items
                SET detected_intent = ?, intent_confidence = ?, status = ?, clarification_question = ?,
                    normalized_summary = ?, domain = ?, project_key = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    classification["intent"],
                    classification["confidence"],
                    classification["status"],
                    classification["clarification_question"],
                    classification["normalized_summary"],
                    classification["domain"],
                    classification["project_key"],
                    timestamp,
                    inbox_item_id,
                ),
            )

            task_id = self._insert_task(conn, inbox_item_id, plan["task"], timestamp)
            memory_item_id = self._insert_memory(conn, inbox_item_id, plan["memory"], timestamp)
            self._insert_artifacts(conn, inbox_item_id, plan["artifacts"], timestamp)
            self._insert_project_links(conn, inbox_item_id, memory_item_id, plan, timestamp)

        return {
            "inbox_item_id": inbox_item_id,
            "task_id": task_id,
            "memory_item_id": memory_item_id,
        }

    def promote_memory(
        self,
        memory_item_id: int,
        *,
        title: str | None = None,
        summary: str | None = None,
        distilled_knowledge: str | None = None,
        scope: str | None = None,
        importance: int | None = None,
    ) -> sqlite3.Row:
        timestamp = utc_now()
        with self.connection() as conn:
            row = conn.execute(
                "SELECT * FROM memory_items WHERE id = ?",
                (memory_item_id,),
            ).fetchone()
            if row is None:
                raise ValueError(f"Memory item {memory_item_id} not found")

            new_title = title or row["title"]
            new_summary = summary or row["summary"]
            new_distilled = distilled_knowledge or row["distilled_knowledge"]
            new_scope = scope or row["scope"]
            new_importance = importance if importance is not None else row["importance"]

            conn.execute(
                """
                UPDATE memory_items
                SET title = ?, summary = ?, distilled_knowledge = ?, scope = ?,
                    importance = ?, status = 'ready', updated_at = ?
                WHERE id = ?
                """,
                (
                    new_title,
                    new_summary,
                    new_distilled,
                    new_scope,
                    new_importance,
                    timestamp,
                    memory_item_id,
                ),
            )
            return conn.execute(
                "SELECT * FROM memory_items WHERE id = ?",
                (memory_item_id,),
            ).fetchone()

    def _insert_task(self, conn: sqlite3.Connection, inbox_item_id: int, task: dict | None, timestamp: str) -> int | None:
        if not task:
            return None
        cursor = conn.execute(
            """
            INSERT INTO tasks (
                inbox_item_id, task_type, status, title, details, project_key, due_hint,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                inbox_item_id,
                task["task_type"],
                task["status"],
                task["title"],
                task["details"],
                task["project_key"],
                task.get("due_hint"),
                timestamp,
                timestamp,
            ),
        )
        return cursor.lastrowid

    def _insert_memory(self, conn: sqlite3.Connection, inbox_item_id: int, memory: dict | None, timestamp: str) -> int | None:
        if not memory:
            return None
        cursor = conn.execute(
            """
            INSERT INTO memory_items (
                inbox_item_id, memory_kind, title, summary, distilled_knowledge, domain,
                scope, project_key, importance, confidence, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                inbox_item_id,
                memory["memory_kind"],
                memory["title"],
                memory["summary"],
                memory["distilled_knowledge"],
                memory["domain"],
                memory["scope"],
                memory["project_key"],
                memory["importance"],
                memory["confidence"],
                memory["status"],
                timestamp,
                timestamp,
            ),
        )
        return cursor.lastrowid

    def _insert_artifacts(self, conn: sqlite3.Connection, inbox_item_id: int, artifacts: list[dict], timestamp: str) -> None:
        for artifact in artifacts:
            conn.execute(
                """
                INSERT INTO artifacts (inbox_item_id, artifact_type, value, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    inbox_item_id,
                    artifact["artifact_type"],
                    artifact["value"],
                    artifact["metadata_json"],
                    timestamp,
                ),
            )

    def _insert_project_links(
        self,
        conn: sqlite3.Connection,
        inbox_item_id: int,
        memory_item_id: int | None,
        plan: dict,
        timestamp: str,
    ) -> None:
        for project_key in plan["context"]["project_keys"]:
            relation_type = "derived_from_input" if memory_item_id else "mentioned_in_input"
            conn.execute(
                """
                INSERT INTO project_links (
                    inbox_item_id, memory_item_id, project_key, relation_type, confidence, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    inbox_item_id,
                    memory_item_id,
                    project_key,
                    relation_type,
                    plan["classification"]["confidence"],
                    timestamp,
                ),
            )

    def _delete_derived_records(self, conn: sqlite3.Connection, inbox_item_id: int) -> None:
        conn.execute("DELETE FROM tasks WHERE inbox_item_id = ?", (inbox_item_id,))
        conn.execute("DELETE FROM project_links WHERE inbox_item_id = ?", (inbox_item_id,))
        conn.execute("DELETE FROM artifacts WHERE inbox_item_id = ?", (inbox_item_id,))
        conn.execute("DELETE FROM memory_items WHERE inbox_item_id = ?", (inbox_item_id,))

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
            "project_improvements", "project_distillations", "skill_references",
        }
        if table not in allowed_tables:
            raise ValueError(f"Unsupported table: {table}")
        with self.connection() as conn:
            cursor = conn.execute(f"SELECT * FROM {table} WHERE id = ?", (record_id,))
            return cursor.fetchone()
