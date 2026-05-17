from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta

from july.storage.utils import utc_now

STALE_SESSION_HOURS = 48
OPEN_SESSION_STATUSES = ("active", "summarized")
TOUCHABLE_SESSION_STATUSES = ("active", "summarized", "stale")


class SessionRepository:
    def __init__(self, connection_factory):
        self.connection = connection_factory

    def session_start(
        self,
        session_key: str,
        *,
        project_key: str | None = None,
        agent_name: str | None = None,
        goal: str | None = None,
    ) -> dict:
        timestamp = utc_now()
        with self.connection() as conn:
            existing = conn.execute(
                "SELECT * FROM sessions WHERE session_key = ?", (session_key,)
            ).fetchone()
            if existing:
                return {"session_id": existing["id"], "status": "already_active", "started_at": existing["started_at"]}
            cursor = conn.execute(
                """
                INSERT INTO sessions (session_key, project_key, agent_name, goal, status, started_at, updated_at)
                VALUES (?, ?, ?, ?, 'active', ?, ?)
                """,
                (session_key, project_key, agent_name, goal, timestamp, timestamp),
            )
        return {"session_id": cursor.lastrowid, "status": "active", "started_at": timestamp}

    def session_summary(
        self,
        session_key: str,
        *,
        summary: str,
        discoveries: str | None = None,
        accomplished: str | None = None,
        next_steps: str | None = None,
        relevant_files: str | None = None,
    ) -> dict:
        timestamp = utc_now()
        with self.connection() as conn:
            row = conn.execute(
                "SELECT * FROM sessions WHERE session_key = ?", (session_key,)
            ).fetchone()
            if row is None:
                raise ValueError(f"Session '{session_key}' not found")
            conn.execute(
                """
                UPDATE sessions
                SET summary = ?, discoveries = ?, accomplished = ?,
                    next_steps = ?, relevant_files = ?, status = 'summarized',
                    updated_at = ?
                WHERE session_key = ?
                """,
                (summary, discoveries, accomplished, next_steps, relevant_files, timestamp, session_key),
            )
        return {"session_key": session_key, "status": "summarized", "summarized_at": timestamp}

    def session_end(self, session_key: str) -> dict:
        timestamp = utc_now()
        with self.connection() as conn:
            row = conn.execute(
                "SELECT * FROM sessions WHERE session_key = ?", (session_key,)
            ).fetchone()
            if row is None:
                raise ValueError(f"Session '{session_key}' not found")
            conn.execute(
                """
                UPDATE sessions
                SET status = CASE
                        WHEN summary IS NOT NULL AND TRIM(summary) <> '' THEN 'closed'
                        ELSE 'closed_without_summary'
                    END,
                    updated_at = ?,
                    ended_at = COALESCE(ended_at, ?)
                WHERE session_key = ?
                """,
                (timestamp, timestamp, session_key),
            )
            updated = conn.execute(
                "SELECT project_key, status, ended_at FROM sessions WHERE session_key = ?",
                (session_key,),
            ).fetchone()
        return {
            "session_key": session_key,
            "project_key": updated["project_key"],
            "status": updated["status"],
            "ended_at": updated["ended_at"],
        }

    def session_context(self, project_key: str | None = None, limit: int = 5) -> list[dict]:
        self.mark_stale_sessions(project_key=project_key)
        with self.connection() as conn:
            if project_key:
                rows = conn.execute(
                    """
                    SELECT id, session_key, project_key, agent_name, goal, status,
                           summary, discoveries, next_steps, started_at, updated_at, ended_at
                    FROM sessions
                    WHERE project_key = ?
                    ORDER BY id DESC LIMIT ?
                    """,
                    (project_key, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT id, session_key, project_key, agent_name, goal, status,
                           summary, discoveries, next_steps, started_at, updated_at, ended_at
                    FROM sessions
                    ORDER BY id DESC LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
        return [self.with_staleness(dict(r)) for r in rows]

    def get_open_session(self, project_key: str) -> dict | None:
        self.mark_stale_sessions(project_key=project_key)
        with self.connection() as conn:
            row = conn.execute(
                """
                SELECT id, session_key, project_key, agent_name, goal, status,
                       summary, discoveries, accomplished, next_steps, relevant_files,
                       started_at, updated_at, ended_at
                FROM sessions
                WHERE project_key = ? AND ended_at IS NULL AND status IN ('active', 'summarized')
                ORDER BY id DESC
                LIMIT 1
                """,
                (project_key,),
            ).fetchone()
        return self.with_staleness(dict(row)) if row is not None else None

    def touch_project_session(self, project_key: str) -> dict | None:
        timestamp = utc_now()
        with self.connection() as conn:
            row = conn.execute(
                f"""
                SELECT id
                FROM sessions
                WHERE project_key = ?
                  AND ended_at IS NULL
                  AND status IN ({", ".join("?" for _ in TOUCHABLE_SESSION_STATUSES)})
                ORDER BY id DESC
                LIMIT 1
                """,
                (project_key, *TOUCHABLE_SESSION_STATUSES),
            ).fetchone()
            if row is None:
                return None
            conn.execute(
                """
                UPDATE sessions
                SET updated_at = ?,
                    status = CASE WHEN status = 'stale' THEN 'active' ELSE status END
                WHERE id = ?
                """,
                (timestamp, row["id"]),
            )
            updated = conn.execute(
                """
                SELECT id, session_key, project_key, agent_name, goal, status,
                       summary, discoveries, accomplished, next_steps, relevant_files,
                       started_at, updated_at, ended_at
                FROM sessions
                WHERE id = ?
                """,
                (row["id"],),
            ).fetchone()
        return self.with_staleness(dict(updated)) if updated is not None else None

    def mark_stale_sessions(self, project_key: str | None = None) -> int:
        cutoff = stale_cutoff()
        query = f"""
            UPDATE sessions
            SET status = 'stale'
            WHERE ended_at IS NULL
              AND status IN ({", ".join("?" for _ in OPEN_SESSION_STATUSES)})
              AND updated_at < ?
        """
        params: list[object] = [*OPEN_SESSION_STATUSES, cutoff]
        if project_key:
            query += " AND project_key = ?"
            params.append(project_key)
        with self.connection() as conn:
            cursor = conn.execute(query, tuple(params))
        return cursor.rowcount

    def list_sessions(self, status: str | None = None, limit: int = 20) -> list[sqlite3.Row]:
        self.mark_stale_sessions()
        query = """
            SELECT id, session_key, project_key, agent_name, goal, status, started_at, updated_at, ended_at
            FROM sessions
        """
        params: list[object] = []
        if status:
            query += " WHERE status = ?"
            params.append(status)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        with self.connection() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
        return [self.with_staleness(dict(row)) for row in rows]

    def with_staleness(self, row: dict) -> dict:
        row["is_stale"] = row.get("status") == "stale"
        row["stale_after_hours"] = STALE_SESSION_HOURS
        return row


def stale_cutoff() -> str:
    return (datetime.now(UTC) - timedelta(hours=STALE_SESSION_HOURS)).replace(microsecond=0).isoformat()
