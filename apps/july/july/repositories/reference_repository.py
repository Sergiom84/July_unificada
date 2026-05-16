from __future__ import annotations

import sqlite3

from july.storage.utils import utc_now


class ReferenceRepository:
    def __init__(self, connection_factory):
        self.connection = connection_factory

    def save_model_contribution(
        self,
        model_name: str,
        contribution_type: str,
        title: str,
        content: str,
        *,
        inbox_item_id: int | None = None,
        memory_item_id: int | None = None,
        session_id: int | None = None,
        project_key: str | None = None,
        domain: str | None = None,
        adopted: bool = False,
        notes: str | None = None,
    ) -> dict:
        timestamp = utc_now()
        with self.connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO model_contributions (
                    model_name, contribution_type, title, content,
                    inbox_item_id, memory_item_id, session_id,
                    project_key, domain, adopted, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    model_name, contribution_type, title, content,
                    inbox_item_id, memory_item_id, session_id,
                    project_key, domain, int(adopted), notes, timestamp,
                ),
            )
        return {"contribution_id": cursor.lastrowid, "model_name": model_name}

    def list_model_contributions(
        self, model_name: str | None = None, project_key: str | None = None, limit: int = 20
    ) -> list[sqlite3.Row]:
        query = """
            SELECT id, model_name, contribution_type, title, project_key, domain, adopted, created_at
            FROM model_contributions
        """
        clauses: list[str] = []
        params: list[object] = []
        if model_name:
            clauses.append("model_name = ?")
            params.append(model_name)
        if project_key:
            clauses.append("project_key = ?")
            params.append(project_key)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        with self.connection() as conn:
            return conn.execute(query, tuple(params)).fetchall()

    def adopt_contribution(self, contribution_id: int, notes: str | None = None) -> dict:
        with self.connection() as conn:
            row = conn.execute(
                "SELECT * FROM model_contributions WHERE id = ?", (contribution_id,)
            ).fetchone()
            if row is None:
                raise ValueError(f"Contribution {contribution_id} not found")
            conn.execute(
                "UPDATE model_contributions SET adopted = 1, notes = COALESCE(?, notes) WHERE id = ?",
                (notes, contribution_id),
            )
        return {"adopted": True, "contribution_id": contribution_id}

    def save_url_metadata(
        self,
        url: str,
        *,
        artifact_id: int | None = None,
        resolved_title: str | None = None,
        description: str | None = None,
        content_type: str | None = None,
        extracted_text: str | None = None,
        youtube_video_id: str | None = None,
        youtube_channel: str | None = None,
        youtube_duration: str | None = None,
        fetch_status: str = "fetched",
    ) -> dict:
        timestamp = utc_now()
        with self.connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO url_metadata (
                    artifact_id, url, resolved_title, description, content_type,
                    extracted_text, youtube_video_id, youtube_channel, youtube_duration,
                    fetch_status, fetched_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    artifact_id, url, resolved_title, description, content_type,
                    extracted_text, youtube_video_id, youtube_channel, youtube_duration,
                    fetch_status, timestamp, timestamp,
                ),
            )
        return {"url_metadata_id": cursor.lastrowid, "url": url, "fetch_status": fetch_status}

    def get_url_metadata(self, url: str) -> sqlite3.Row | None:
        with self.connection() as conn:
            return conn.execute(
                "SELECT * FROM url_metadata WHERE url = ? ORDER BY id DESC LIMIT 1",
                (url,),
            ).fetchone()

    def save_external_reference(
        self,
        source_url: str,
        source_name: str,
        reference_type: str,
        title: str,
        *,
        description: str | None = None,
        relevance_note: str | None = None,
        inbox_item_id: int | None = None,
        memory_item_id: int | None = None,
        project_key: str | None = None,
    ) -> dict:
        timestamp = utc_now()
        with self.connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO external_references (
                    source_url, source_name, reference_type, title,
                    description, relevance_note, inbox_item_id, memory_item_id,
                    project_key, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source_url, source_name, reference_type, title,
                    description, relevance_note, inbox_item_id, memory_item_id,
                    project_key, timestamp,
                ),
            )
        return {"external_reference_id": cursor.lastrowid, "source_name": source_name}

    def list_external_references(self, project_key: str | None = None, limit: int = 20) -> list[sqlite3.Row]:
        if project_key:
            query = """
                SELECT id, source_url, source_name, reference_type, title, relevance_note, project_key, created_at
                FROM external_references WHERE project_key = ? ORDER BY id DESC LIMIT ?
            """
            params: tuple = (project_key, limit)
        else:
            query = """
                SELECT id, source_url, source_name, reference_type, title, relevance_note, project_key, created_at
                FROM external_references ORDER BY id DESC LIMIT ?
            """
            params = (limit,)
        with self.connection() as conn:
            return conn.execute(query, params).fetchall()
