from __future__ import annotations

import sqlite3

from july.storage.utils import utc_now


class TopicRepository:
    def __init__(self, connection_factory):
        self.connection = connection_factory

    def create_topic(self, topic_key: str, label: str, domain: str, description: str | None = None) -> dict:
        timestamp = utc_now()
        with self.connection() as conn:
            existing = conn.execute(
                "SELECT * FROM topic_keys WHERE topic_key = ?", (topic_key,)
            ).fetchone()
            if existing:
                return {"topic_id": existing["id"], "status": "already_exists"}
            cursor = conn.execute(
                """
                INSERT INTO topic_keys (topic_key, label, domain, description, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (topic_key, label, domain, description, timestamp, timestamp),
            )
        return {"topic_id": cursor.lastrowid, "status": "created"}

    def link_to_topic(
        self,
        topic_key: str,
        *,
        inbox_item_id: int | None = None,
        memory_item_id: int | None = None,
        session_id: int | None = None,
    ) -> dict:
        timestamp = utc_now()
        with self.connection() as conn:
            topic = conn.execute(
                "SELECT id FROM topic_keys WHERE topic_key = ?", (topic_key,)
            ).fetchone()
            if topic is None:
                raise ValueError(f"Topic '{topic_key}' not found")
            conn.execute(
                """
                INSERT INTO topic_links (topic_key_id, inbox_item_id, memory_item_id, session_id, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (topic["id"], inbox_item_id, memory_item_id, session_id, timestamp),
            )
        return {"linked": True, "topic_key": topic_key}

    def topic_context(self, topic_key: str, limit: int = 20) -> dict:
        with self.connection() as conn:
            topic = conn.execute(
                "SELECT * FROM topic_keys WHERE topic_key = ?", (topic_key,)
            ).fetchone()
            if topic is None:
                raise ValueError(f"Topic '{topic_key}' not found")
            links = conn.execute(
                """
                SELECT tl.id, tl.inbox_item_id, tl.memory_item_id, tl.session_id, tl.created_at
                FROM topic_links tl
                WHERE tl.topic_key_id = ?
                ORDER BY tl.id DESC LIMIT ?
                """,
                (topic["id"], limit),
            ).fetchall()
            memory_ids = [link["memory_item_id"] for link in links if link["memory_item_id"]]
            memories = []
            for memory_id in memory_ids:
                row = conn.execute(
                    "SELECT id, memory_kind, status, title, summary, domain, scope, project_key FROM memory_items WHERE id = ?",
                    (memory_id,),
                ).fetchone()
                if row:
                    memories.append(dict(row))
        return {"topic": dict(topic), "links": [dict(link) for link in links], "memories": memories}

    def list_topics(self, limit: int = 50) -> list[sqlite3.Row]:
        with self.connection() as conn:
            return conn.execute(
                "SELECT id, topic_key, label, domain, description, created_at FROM topic_keys ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
