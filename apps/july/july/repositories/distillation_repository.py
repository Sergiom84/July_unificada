from __future__ import annotations

import json
from typing import Any

from july.storage.utils import utc_now

DISTILLATION_SESSION_THRESHOLD = 5


class DistillationRepository:
    def __init__(self, connection_factory):
        self.connection = connection_factory

    def distill_candidates(
        self,
        project_key: str,
        *,
        threshold: int = DISTILLATION_SESSION_THRESHOLD,
        limit: int = 10,
    ) -> dict[str, Any]:
        with self.connection() as conn:
            last = conn.execute(
                """
                SELECT *
                FROM project_distillations
                WHERE project_key = ?
                ORDER BY to_session_id DESC, id DESC
                LIMIT 1
                """,
                (project_key,),
            ).fetchone()
            last_to_session_id = int(last["to_session_id"] or 0) if last else 0
            closed_sessions = conn.execute(
                """
                SELECT id, session_key, status, summary, discoveries, next_steps, started_at, ended_at
                FROM sessions
                WHERE project_key = ?
                  AND status IN ('closed', 'closed_without_summary')
                  AND id > ?
                ORDER BY id ASC
                """,
                (project_key, last_to_session_id),
            ).fetchall()
            since_timestamp = last["distilled_at"] if last else None
            candidates = {
                "decisions": self._memory_candidates(conn, project_key, since_timestamp, limit, "decision"),
                "resolved_errors": self._memory_candidates(conn, project_key, since_timestamp, limit, "resolved_error"),
                "workflows": self._memory_candidates(conn, project_key, since_timestamp, limit, "workflow"),
                "patterns": self._memory_candidates(conn, project_key, since_timestamp, limit, "pattern"),
                "improvements": self._improvement_candidates(conn, project_key, since_timestamp, limit),
                "pendings": self._pending_candidates(conn, project_key, since_timestamp, limit),
            }

        session_count = len(closed_sessions)
        candidate_counts = {key: len(value) for key, value in candidates.items()}
        strong_count = (
            candidate_counts["decisions"]
            + candidate_counts["resolved_errors"]
            + candidate_counts["workflows"]
            + candidate_counts["patterns"]
        )
        reasons: list[str] = []
        if session_count >= threshold:
            reasons.append(f"{session_count} sesiones cerradas desde el último destilado")
        if strong_count:
            reasons.append(f"{strong_count} hallazgos duraderos candidatos a wiki")

        from_session_id = closed_sessions[0]["id"] if closed_sessions else None
        to_session_id = closed_sessions[-1]["id"] if closed_sessions else last_to_session_id or None

        return {
            "project_key": project_key,
            "threshold": threshold,
            "needs_distillation": bool(reasons),
            "reasons": reasons,
            "last_distillation": dict(last) if last else None,
            "sessions_since_last": session_count,
            "window": {
                "from_session_id": from_session_id,
                "to_session_id": to_session_id,
                "since_timestamp": since_timestamp,
            },
            "recent_sessions": [dict(row) for row in closed_sessions[-limit:]],
            "candidate_counts": candidate_counts,
            "candidates": candidates,
        }

    def record_distillation(
        self,
        project_key: str,
        *,
        wiki_pages_changed: list[str] | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        timestamp = utc_now()
        state = self.distill_candidates(project_key, limit=1)
        from_session_id = state["window"]["from_session_id"]
        to_session_id = state["window"]["to_session_id"]
        session_count = state["sessions_since_last"]
        pages_json = json.dumps(wiki_pages_changed or [], ensure_ascii=True)

        with self.connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO project_distillations (
                    project_key, from_session_id, to_session_id, session_count,
                    wiki_pages_changed_json, notes, distilled_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_key,
                    from_session_id,
                    to_session_id,
                    session_count,
                    pages_json,
                    notes,
                    timestamp,
                    timestamp,
                ),
            )
            row = conn.execute(
                "SELECT * FROM project_distillations WHERE id = ?",
                (cursor.lastrowid,),
            ).fetchone()
        return self._distillation_row(row)

    def list_distillations(self, project_key: str, *, limit: int = 10) -> list[dict[str, Any]]:
        with self.connection() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM project_distillations
                WHERE project_key = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (project_key, limit),
            ).fetchall()
        return [self._distillation_row(row) for row in rows]

    def _memory_candidates(self, conn, project_key: str, since: str | None, limit: int, kind: str) -> list[dict[str, Any]]:
        filters = {
            "decision": "LOWER(title) LIKE 'decision%' OR LOWER(title) LIKE 'decisión%' OR LOWER(summary) LIKE '%decision%' OR LOWER(summary) LIKE '%decisión%' OR LOWER(distilled_knowledge) LIKE '%decision%' OR LOWER(distilled_knowledge) LIKE '%decisión%'",
            "resolved_error": "LOWER(title) LIKE 'error resuelto%' OR LOWER(summary) LIKE '%resuelto%' OR LOWER(distilled_knowledge) LIKE '%resuelto%'",
            "workflow": "LOWER(title) LIKE 'mejora de flujo%' OR LOWER(summary) LIKE '%workflow%' OR LOWER(summary) LIKE '%flujo%' OR LOWER(distilled_knowledge) LIKE '%workflow%' OR LOWER(distilled_knowledge) LIKE '%flujo%'",
            "pattern": "LOWER(title) LIKE 'hallazgo%' OR LOWER(summary) LIKE '%patron%' OR LOWER(summary) LIKE '%patrón%' OR LOWER(distilled_knowledge) LIKE '%reutilizable%' OR LOWER(distilled_knowledge) LIKE '%patron%' OR LOWER(distilled_knowledge) LIKE '%patrón%'",
        }
        where = filters[kind]
        params: list[object] = [project_key]
        query = f"""
            SELECT id, memory_kind, title, summary, distilled_knowledge, created_at
            FROM memory_items
            WHERE project_key = ?
              AND ({where})
        """
        if since:
            query += " AND created_at > ?"
            params.append(since)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(query, tuple(params)).fetchall()
        return [
            {
                "source": "memory_items",
                "id": row["id"],
                "kind": kind,
                "title": row["title"],
                "summary": row["summary"],
                "detail": row["distilled_knowledge"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def _improvement_candidates(self, conn, project_key: str, since: str | None, limit: int) -> list[dict[str, Any]]:
        params: list[object] = [project_key]
        query = """
            SELECT id, title, description, status, priority, updated_at
            FROM project_improvements
            WHERE project_key = ?
              AND status IN ('planned', 'in_progress', 'done')
        """
        if since:
            query += " AND updated_at > ?"
            params.append(since)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(query, tuple(params)).fetchall()
        return [
            {
                "source": "project_improvements",
                "id": row["id"],
                "kind": "improvement",
                "title": row["title"],
                "summary": row["description"],
                "status": row["status"],
                "priority": row["priority"],
                "created_at": row["updated_at"],
            }
            for row in rows
        ]

    def _pending_candidates(self, conn, project_key: str, since: str | None, limit: int) -> list[dict[str, Any]]:
        params: list[object] = [project_key]
        query = """
            SELECT id, title, details, status, updated_at
            FROM tasks
            WHERE project_key = ?
              AND task_type = 'manual_follow_up'
              AND status IN ('in_progress', 'done')
        """
        if since:
            query += " AND updated_at > ?"
            params.append(since)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(query, tuple(params)).fetchall()
        return [
            {
                "source": "tasks",
                "id": row["id"],
                "kind": "pending",
                "title": row["title"],
                "summary": row["details"],
                "status": row["status"],
                "created_at": row["updated_at"],
            }
            for row in rows
        ]

    def _distillation_row(self, row) -> dict[str, Any]:
        result = dict(row)
        result["wiki_pages_changed"] = json.loads(result.pop("wiki_pages_changed_json") or "[]")
        return result
