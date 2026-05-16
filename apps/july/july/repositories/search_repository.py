from __future__ import annotations

import sqlite3
from collections.abc import Callable


class SearchRepository:
    def __init__(self, connection_factory, skill_suggestion_provider: Callable | None = None):
        self.connection = connection_factory
        self.skill_suggestion_provider = skill_suggestion_provider

    def search(self, query: str, limit: int = 10) -> dict[str, list[sqlite3.Row]]:
        with self.connection() as conn:
            try:
                inbox_rows = conn.execute(
                    """
                    SELECT inbox_items.id, inbox_items.detected_intent, inbox_items.status,
                           inbox_items.domain, inbox_items.project_key, inbox_items.normalized_summary
                    FROM inbox_items_fts
                    JOIN inbox_items ON inbox_items_fts.rowid = inbox_items.id
                    WHERE inbox_items_fts MATCH ?
                    ORDER BY inbox_items.id DESC
                    LIMIT ?
                    """,
                    (query, limit),
                ).fetchall()

                memory_rows = conn.execute(
                    """
                    SELECT memory_items.id, memory_items.memory_kind, memory_items.status,
                           memory_items.domain, memory_items.scope, memory_items.project_key, memory_items.title
                    FROM memory_items_fts
                    JOIN memory_items ON memory_items_fts.rowid = memory_items.id
                    WHERE memory_items_fts MATCH ?
                    ORDER BY memory_items.id DESC
                    LIMIT ?
                    """,
                    (query, limit),
                ).fetchall()
            except sqlite3.OperationalError:
                inbox_rows = conn.execute(
                    """
                    SELECT id, detected_intent, status, domain, project_key, normalized_summary
                    FROM inbox_items
                    WHERE raw_input LIKE ? OR normalized_summary LIKE ?
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (f"%{query}%", f"%{query}%", limit),
                ).fetchall()
                memory_rows = conn.execute(
                    """
                    SELECT id, memory_kind, status, domain, scope, project_key, title
                    FROM memory_items
                    WHERE title LIKE ? OR summary LIKE ? OR distilled_knowledge LIKE ?
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (f"%{query}%", f"%{query}%", f"%{query}%", limit),
                ).fetchall()

            task_rows = conn.execute(
                """
                SELECT id, inbox_item_id, task_type, status, project_key, title
                FROM tasks
                WHERE title LIKE ? OR details LIKE ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (f"%{query}%", f"%{query}%", limit),
            ).fetchall()
            improvement_rows = conn.execute(
                """
                SELECT id, project_key, title, status, priority, created_at
                FROM project_improvements
                WHERE title LIKE ? OR description LIKE ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (f"%{query}%", f"%{query}%", limit),
            ).fetchall()

        return {"inbox": inbox_rows, "memory": memory_rows, "tasks": task_rows, "improvements": improvement_rows}

    def proactive_recall(self, raw_input: str, project_key: str | None = None, limit: int = 5) -> dict:
        words = [word for word in raw_input.lower().split() if len(word) > 3]
        if not words:
            return {
                "related_memories": [],
                "related_sessions": [],
                "suggestions": [],
                "skill_suggestions": self._suggest_skills(raw_input, project_key, limit),
            }

        with self.connection() as conn:
            fts_query = " OR ".join(words[:8])
            try:
                memory_rows = conn.execute(
                    """
                    SELECT memory_items.id, memory_items.memory_kind, memory_items.status,
                           memory_items.domain, memory_items.scope, memory_items.project_key,
                           memory_items.title, memory_items.summary, memory_items.distilled_knowledge
                    FROM memory_items_fts
                    JOIN memory_items ON memory_items_fts.rowid = memory_items.id
                    WHERE memory_items_fts MATCH ?
                    ORDER BY memory_items.importance DESC, memory_items.id DESC
                    LIMIT ?
                    """,
                    (fts_query, limit),
                ).fetchall()
            except sqlite3.OperationalError:
                like_pattern = f"%{words[0]}%"
                memory_rows = conn.execute(
                    """
                    SELECT id, memory_kind, status, domain, scope, project_key,
                           title, summary, distilled_knowledge
                    FROM memory_items
                    WHERE title LIKE ? OR summary LIKE ? OR distilled_knowledge LIKE ?
                    ORDER BY importance DESC, id DESC
                    LIMIT ?
                    """,
                    (like_pattern, like_pattern, like_pattern, limit),
                ).fetchall()

            session_rows = []
            if project_key:
                session_rows = conn.execute(
                    """
                    SELECT id, session_key, project_key, goal, status, summary, next_steps, started_at
                    FROM sessions
                    WHERE project_key = ? AND summary IS NOT NULL
                    ORDER BY id DESC LIMIT 3
                    """,
                    (project_key,),
                ).fetchall()

            suggestions = []
            for memory in memory_rows:
                if memory["status"] == "ready" and memory["scope"] == "global":
                    suggestions.append({
                        "type": "reuse_memory",
                        "memory_id": memory["id"],
                        "title": memory["title"],
                        "reason": f"Memoria global reutilizable: {memory['distilled_knowledge'][:120]}",
                    })
                elif memory["project_key"] and memory["project_key"] != project_key:
                    suggestions.append({
                        "type": "cross_project",
                        "memory_id": memory["id"],
                        "title": memory["title"],
                        "from_project": memory["project_key"],
                        "reason": f"Ya resolviste algo parecido en {memory['project_key']}: {memory['title']}",
                    })

        return {
            "related_memories": [dict(row) for row in memory_rows],
            "related_sessions": [dict(row) for row in session_rows],
            "suggestions": suggestions,
            "skill_suggestions": self._suggest_skills(raw_input, project_key, limit),
        }

    def _suggest_skills(self, raw_input: str, project_key: str | None, limit: int) -> list[dict]:
        if self.skill_suggestion_provider is None:
            return []
        return self.skill_suggestion_provider(raw_input, project_key=project_key, limit=limit)
