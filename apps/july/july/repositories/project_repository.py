from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from july.storage.utils import utc_now


class ProjectRepository:
    def __init__(self, connection_factory):
        self.connection = connection_factory

    def project_context(self, project_key: str, limit: int = 10) -> dict[str, list[sqlite3.Row]]:
        with self.connection() as conn:
            inbox_rows = conn.execute(
                """
                SELECT id, detected_intent, status, normalized_summary, created_at
                FROM inbox_items
                WHERE project_key = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (project_key, limit),
            ).fetchall()
            task_rows = conn.execute(
                """
                SELECT id, task_type, status, title, created_at
                FROM tasks
                WHERE project_key = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (project_key, limit),
            ).fetchall()
            memory_rows = conn.execute(
                """
                SELECT id, memory_kind, status, title, summary, created_at
                FROM memory_items
                WHERE project_key = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (project_key, limit),
            ).fetchall()
            improvement_rows = conn.execute(
                """
                SELECT id, title, description, status, priority, created_at, updated_at
                FROM project_improvements
                WHERE project_key = ?
                  AND status IN ('open', 'planned', 'in_progress')
                ORDER BY
                    CASE priority
                        WHEN 'high' THEN 0
                        WHEN 'normal' THEN 1
                        ELSE 2
                    END,
                    id DESC
                LIMIT ?
                """,
                (project_key, limit),
            ).fetchall()
        return {"inbox": inbox_rows, "tasks": task_rows, "memory": memory_rows, "improvements": improvement_rows}

    def upsert_project(
        self,
        project_key: str,
        repo_root: str,
        *,
        repo_name: str | None = None,
        display_name: str | None = None,
        project_kind: str | None = None,
        project_tags: list[str] | None = None,
        preferences: dict | None = None,
    ) -> dict:
        timestamp = utc_now()
        normalized_repo_root = str(Path(repo_root).resolve())
        normalized_repo_name = repo_name or Path(normalized_repo_root).name
        normalized_display_name = display_name or normalized_repo_name or project_key.replace("-", " ").title()
        normalized_project_kind = project_kind or "unknown"
        project_tags_json = json.dumps(sorted(set(project_tags or [])), ensure_ascii=True)
        preferences_json = json.dumps(preferences or {}, ensure_ascii=True, sort_keys=True)

        with self.connection() as conn:
            existing = conn.execute(
                "SELECT * FROM projects WHERE project_key = ?",
                (project_key,),
            ).fetchone()
            if existing is None:
                conn.execute(
                    """
                    INSERT INTO projects (
                        project_key, repo_root, repo_name, display_name, project_kind,
                        project_tags_json, preferences_json,
                        created_at, updated_at, last_seen_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        project_key,
                        normalized_repo_root,
                        normalized_repo_name,
                        normalized_display_name,
                        normalized_project_kind,
                        project_tags_json,
                        preferences_json,
                        timestamp,
                        timestamp,
                        timestamp,
                    ),
                )
            else:
                updated_at = existing["updated_at"]
                next_project_kind = (
                    normalized_project_kind
                    if normalized_project_kind != "unknown"
                    else existing["project_kind"]
                )
                next_project_tags_json = project_tags_json if project_tags is not None else existing["project_tags_json"]
                next_preferences_json = preferences_json if preferences is not None else existing["preferences_json"]
                if (
                    existing["repo_root"] != normalized_repo_root
                    or existing["repo_name"] != normalized_repo_name
                    or existing["display_name"] != normalized_display_name
                    or existing["project_kind"] != next_project_kind
                    or existing["project_tags_json"] != next_project_tags_json
                    or existing["preferences_json"] != next_preferences_json
                ):
                    updated_at = timestamp
                conn.execute(
                    """
                    UPDATE projects
                    SET repo_root = ?, repo_name = ?, display_name = ?, project_kind = ?,
                        project_tags_json = ?, preferences_json = ?, updated_at = ?, last_seen_at = ?
                    WHERE project_key = ?
                    """,
                    (
                        normalized_repo_root,
                        normalized_repo_name,
                        normalized_display_name,
                        next_project_kind,
                        next_project_tags_json,
                        next_preferences_json,
                        updated_at,
                        timestamp,
                        project_key,
                    ),
                )

            row = conn.execute(
                "SELECT * FROM projects WHERE project_key = ?",
                (project_key,),
            ).fetchone()
        return dict(row) if row is not None else {}

    def touch_project(self, project_key: str) -> dict | None:
        timestamp = utc_now()
        with self.connection() as conn:
            row = conn.execute(
                "SELECT * FROM projects WHERE project_key = ?",
                (project_key,),
            ).fetchone()
            if row is None:
                return None
            conn.execute(
                "UPDATE projects SET last_seen_at = ? WHERE project_key = ?",
                (timestamp, project_key),
            )
            updated = conn.execute(
                "SELECT * FROM projects WHERE project_key = ?",
                (project_key,),
            ).fetchone()
        return dict(updated) if updated is not None else None

    def get_project(self, project_key: str) -> dict | None:
        with self.connection() as conn:
            row = conn.execute(
                "SELECT * FROM projects WHERE project_key = ?",
                (project_key,),
            ).fetchone()
        return dict(row) if row is not None else None

    def list_projects(self, limit: int = 20) -> list[dict]:
        with self.connection() as conn:
            rows = conn.execute(
                """
                SELECT
                    p.*,
                    (
                        SELECT COUNT(*)
                        FROM tasks t
                        WHERE t.project_key = p.project_key AND t.status != 'done'
                    ) AS pending_tasks,
                    (
                        SELECT COUNT(*)
                        FROM project_improvements pi
                        WHERE pi.project_key = p.project_key
                          AND pi.status IN ('open', 'planned', 'in_progress')
                    ) AS open_improvements,
                    (
                        SELECT COUNT(*)
                        FROM memory_items m
                        WHERE m.project_key = p.project_key
                    ) AS memory_items,
                    (
                        SELECT COUNT(*)
                        FROM sessions s
                        WHERE s.project_key = p.project_key
                    ) AS sessions
                FROM projects p
                ORDER BY p.last_seen_at DESC, p.updated_at DESC, p.id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_project_totals(self, project_key: str) -> dict[str, int]:
        with self.connection() as conn:
            row = conn.execute(
                """
                SELECT
                    (
                        SELECT COUNT(*)
                        FROM memory_items m
                        WHERE m.project_key = ?
                    ) AS memory_items,
                    (
                        SELECT COUNT(*)
                        FROM memory_items m
                        WHERE m.project_key = ?
                          AND LOWER(m.title) LIKE 'hallazgo%%'
                    ) AS findings,
                    (
                        SELECT COUNT(*)
                        FROM tasks t
                        WHERE t.project_key = ?
                          AND t.status != 'done'
                    ) AS pending_tasks,
                    (
                        SELECT COUNT(*)
                        FROM project_improvements pi
                        WHERE pi.project_key = ?
                          AND pi.status IN ('open', 'planned', 'in_progress')
                    ) AS open_improvements,
                    (
                        SELECT COUNT(*)
                        FROM sessions s
                        WHERE s.project_key = ?
                    ) AS sessions,
                    (
                        SELECT COUNT(*)
                        FROM inbox_items i
                        WHERE i.project_key = ?
                    ) AS inbox_items
                """,
                (project_key, project_key, project_key, project_key, project_key, project_key),
            ).fetchone()
        return dict(row) if row is not None else {
            "memory_items": 0,
            "findings": 0,
            "pending_tasks": 0,
            "open_improvements": 0,
            "sessions": 0,
            "inbox_items": 0,
        }
