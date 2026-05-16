from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from july.config import Settings
from july.repositories.memory_repository import MemoryRepository
from july.repositories.project_repository import ProjectRepository
from july.repositories.session_repository import SessionRepository
from july.repositories.skill_repository import SkillRepository
from july.repositories.task_repository import TaskRepository
from july.repositories.topic_repository import TopicRepository
from july.storage.schema import SCHEMA_SQL
from july.storage.utils import utc_now


class JulyDatabase:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.settings.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self.projects = ProjectRepository(self.connection)
        self.sessions = SessionRepository(self.connection)
        self.skills = SkillRepository(self.connection)
        self.tasks = TaskRepository(self.connection)
        self.memory = MemoryRepository(self.connection)
        self.topics = TopicRepository(self.connection)

    @contextmanager
    def connection(self):
        conn = sqlite3.connect(self.settings.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self.connection() as conn:
            conn.executescript(SCHEMA_SQL)
            self._migrate_legacy_schema(conn)

    def _migrate_legacy_schema(self, conn: sqlite3.Connection) -> None:
        project_columns = conn.execute("PRAGMA table_info(projects)").fetchall()
        project_column_names = {row["name"] for row in project_columns}
        if "project_kind" not in project_column_names:
            conn.execute("ALTER TABLE projects ADD COLUMN project_kind TEXT NOT NULL DEFAULT 'unknown'")
        if "project_tags_json" not in project_column_names:
            conn.execute("ALTER TABLE projects ADD COLUMN project_tags_json TEXT NOT NULL DEFAULT '[]'")
        if "preferences_json" not in project_column_names:
            conn.execute("ALTER TABLE projects ADD COLUMN preferences_json TEXT NOT NULL DEFAULT '{}'")

        task_columns = conn.execute("PRAGMA table_info(tasks)").fetchall()
        inbox_item_column = next((row for row in task_columns if row["name"] == "inbox_item_id"), None)
        if inbox_item_column and inbox_item_column["notnull"]:
            conn.executescript(
                """
                ALTER TABLE tasks RENAME TO tasks_legacy;

                CREATE TABLE tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    inbox_item_id INTEGER REFERENCES inbox_items(id) ON DELETE CASCADE,
                    task_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    title TEXT NOT NULL,
                    details TEXT,
                    project_key TEXT,
                    due_hint TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                INSERT INTO tasks (
                    id, inbox_item_id, task_type, status, title, details, project_key, due_hint,
                    created_at, updated_at
                )
                SELECT
                    id, inbox_item_id, task_type, status, title, details, project_key, due_hint,
                    created_at, updated_at
                FROM tasks_legacy;

                DROP TABLE tasks_legacy;
                """
            )

    def capture(self, *args, **kwargs):
        return self.memory.capture(*args, **kwargs)

    def resolve_clarification(self, *args, **kwargs):
        return self.memory.resolve_clarification(*args, **kwargs)

    def promote_memory(self, *args, **kwargs):
        return self.memory.promote_memory(*args, **kwargs)

    def project_context(self, *args, **kwargs):
        return self.projects.project_context(*args, **kwargs)

    def upsert_project(self, *args, **kwargs):
        return self.projects.upsert_project(*args, **kwargs)

    def touch_project(self, *args, **kwargs):
        return self.projects.touch_project(*args, **kwargs)

    def get_project(self, *args, **kwargs):
        return self.projects.get_project(*args, **kwargs)

    def list_projects(self, *args, **kwargs):
        return self.projects.list_projects(*args, **kwargs)

    def get_project_totals(self, *args, **kwargs):
        return self.projects.get_project_totals(*args, **kwargs)

    def create_project_improvement(self, *args, **kwargs):
        return self.tasks.create_project_improvement(*args, **kwargs)

    def list_project_improvements(self, *args, **kwargs):
        return self.tasks.list_project_improvements(*args, **kwargs)

    def update_project_improvement_status(self, *args, **kwargs):
        return self.tasks.update_project_improvement_status(*args, **kwargs)

    def create_manual_task(self, *args, **kwargs):
        return self.tasks.create_manual_task(*args, **kwargs)

    def list_project_tasks(self, *args, **kwargs):
        return self.tasks.list_project_tasks(*args, **kwargs)

    def update_task_status(self, *args, **kwargs):
        return self.tasks.update_task_status(*args, **kwargs)

    def list_inbox(self, *args, **kwargs):
        return self.memory.list_inbox(*args, **kwargs)

    def list_tasks(self, *args, **kwargs):
        return self.memory.list_tasks(*args, **kwargs)

    def list_memory(self, *args, **kwargs):
        return self.memory.list_memory(*args, **kwargs)

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

    def get_record(self, *args, **kwargs):
        return self.memory.get_record(*args, **kwargs)

    # ── Session protocol ──────────────────────────────────────────────

    def session_start(self, *args, **kwargs):
        return self.sessions.session_start(*args, **kwargs)

    def session_summary(self, *args, **kwargs):
        return self.sessions.session_summary(*args, **kwargs)

    def session_end(self, *args, **kwargs):
        return self.sessions.session_end(*args, **kwargs)

    def session_context(self, *args, **kwargs):
        return self.sessions.session_context(*args, **kwargs)

    def get_open_session(self, *args, **kwargs):
        return self.sessions.get_open_session(*args, **kwargs)

    def list_sessions(self, *args, **kwargs):
        return self.sessions.list_sessions(*args, **kwargs)

    # ── Topic keys ────────────────────────────────────────────────────

    def create_topic(self, *args, **kwargs):
        return self.topics.create_topic(*args, **kwargs)

    def link_to_topic(self, *args, **kwargs):
        return self.topics.link_to_topic(*args, **kwargs)

    def topic_context(self, *args, **kwargs):
        return self.topics.topic_context(*args, **kwargs)

    def list_topics(self, *args, **kwargs):
        return self.topics.list_topics(*args, **kwargs)

    # ── Model contributions / traceability ────────────────────────────

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

    # ── URL metadata ──────────────────────────────────────────────────

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

    # ── External references (skills.sh, agents.md, etc.) ─────────────

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

    # ── Skill references ─────────────────────────────────────────────

    def upsert_skill_reference(self, *args, **kwargs):
        return self.skills.upsert_skill_reference(*args, **kwargs)

    def list_skill_references(self, *args, **kwargs):
        return self.skills.list_skill_references(*args, **kwargs)

    def suggest_skill_references(self, *args, **kwargs):
        return self.skills.suggest_skill_references(*args, **kwargs)

    # ── Proactive recall ──────────────────────────────────────────────

    def proactive_recall(self, raw_input: str, project_key: str | None = None, limit: int = 5) -> dict:
        """Search memory proactively for related items when a new input arrives."""
        words = [w for w in raw_input.lower().split() if len(w) > 3]
        if not words:
            return {
                "related_memories": [],
                "related_sessions": [],
                "suggestions": [],
                "skill_suggestions": self.suggest_skill_references(raw_input, project_key=project_key, limit=limit),
            }

        with self.connection() as conn:
            # Search in memory via FTS
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

            # Also search recent sessions for relevant context
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

            # Build suggestions
            suggestions = []
            for mem in memory_rows:
                if mem["status"] == "ready" and mem["scope"] == "global":
                    suggestions.append({
                        "type": "reuse_memory",
                        "memory_id": mem["id"],
                        "title": mem["title"],
                        "reason": f"Memoria global reutilizable: {mem['distilled_knowledge'][:120]}",
                    })
                elif mem["project_key"] and mem["project_key"] != project_key:
                    suggestions.append({
                        "type": "cross_project",
                        "memory_id": mem["id"],
                        "title": mem["title"],
                        "from_project": mem["project_key"],
                        "reason": f"Ya resolviste algo parecido en {mem['project_key']}: {mem['title']}",
                    })

        return {
            "related_memories": [dict(r) for r in memory_rows],
            "related_sessions": [dict(r) for r in session_rows],
            "suggestions": suggestions,
            "skill_suggestions": self.suggest_skill_references(raw_input, project_key=project_key, limit=limit),
        }

    def stats(self) -> dict[str, int]:
        with self.connection() as conn:
            return {
                "inbox_items": conn.execute("SELECT COUNT(*) FROM inbox_items").fetchone()[0],
                "tasks": conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0],
                "memory_items": conn.execute("SELECT COUNT(*) FROM memory_items").fetchone()[0],
                "artifacts": conn.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0],
                "project_links": conn.execute("SELECT COUNT(*) FROM project_links").fetchone()[0],
                "clarification_events": conn.execute("SELECT COUNT(*) FROM clarification_events").fetchone()[0],
                "sessions": conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0],
                "topic_keys": conn.execute("SELECT COUNT(*) FROM topic_keys").fetchone()[0],
                "model_contributions": conn.execute("SELECT COUNT(*) FROM model_contributions").fetchone()[0],
                "url_metadata": conn.execute("SELECT COUNT(*) FROM url_metadata").fetchone()[0],
                "external_references": conn.execute("SELECT COUNT(*) FROM external_references").fetchone()[0],
                "skill_references": conn.execute("SELECT COUNT(*) FROM skill_references").fetchone()[0],
                "projects": conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0],
                "project_improvements": conn.execute("SELECT COUNT(*) FROM project_improvements").fetchone()[0],
                "developer_interactions": conn.execute("SELECT COUNT(*) FROM developer_interactions").fetchone()[0],
            }

    # ── Developer profile ──────────────────────────────────────

    def get_developer_profile(self, profile_key: str = "default") -> dict | None:
        with self.connection() as conn:
            row = conn.execute(
                "SELECT * FROM developer_profile WHERE profile_key = ?",
                (profile_key,),
            ).fetchone()
            return dict(row) if row else None

    def ensure_developer_profile(self, profile_key: str = "default") -> dict:
        existing = self.get_developer_profile(profile_key)
        if existing:
            return existing
        timestamp = utc_now()
        with self.connection() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO developer_profile (
                    profile_key, inferred_level, total_interactions,
                    decisions_count, architecture_questions,
                    code_smells_addressed, patterns_applied,
                    last_interaction_at, created_at, updated_at
                ) VALUES (?, 'junior', 0, 0, 0, 0, 0, ?, ?, ?)
                """,
                (profile_key, timestamp, timestamp, timestamp),
            )
        return self.get_developer_profile(profile_key)

    def record_developer_interaction(
        self,
        interaction_type: str,
        *,
        complexity: str = "basic",
        project_key: str | None = None,
        detail: str | None = None,
        profile_key: str = "default",
    ) -> dict:
        timestamp = utc_now()
        self.ensure_developer_profile(profile_key)

        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO developer_interactions (
                    profile_key, interaction_type, complexity, project_key, detail, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (profile_key, interaction_type, complexity, project_key, detail, timestamp),
            )

            # Update counters
            increment_field = {
                "decision": "decisions_count",
                "architecture_question": "architecture_questions",
                "smell_fix": "code_smells_addressed",
                "pattern_apply": "patterns_applied",
            }.get(interaction_type)

            update_parts = [
                "total_interactions = total_interactions + 1",
                "last_interaction_at = ?",
                "updated_at = ?",
            ]
            params: list = [timestamp, timestamp]

            if increment_field:
                update_parts.append(f"{increment_field} = {increment_field} + 1")

            conn.execute(
                f"UPDATE developer_profile SET {', '.join(update_parts)} WHERE profile_key = ?",
                (*params, profile_key),
            )

        return self._infer_and_update_level(profile_key)

    def _infer_and_update_level(self, profile_key: str = "default") -> dict:
        profile = self.get_developer_profile(profile_key)
        if not profile:
            return {"level": "junior", "profile": None}

        total = profile["total_interactions"]
        decisions = profile["decisions_count"]
        arch_q = profile["architecture_questions"]
        smells = profile["code_smells_addressed"]
        patterns = profile["patterns_applied"]

        # Inference logic
        score = 0
        score += min(total // 10, 5)  # Up to 5 points for volume
        score += min(decisions // 3, 4)  # Up to 4 points for decisions
        score += min(arch_q // 2, 3)  # Up to 3 for architecture engagement
        score += min(smells // 2, 3)  # Up to 3 for addressing smells
        score += min(patterns // 2, 3)  # Up to 3 for applying patterns

        if score >= 12:
            level = "senior"
        elif score >= 5:
            level = "mid"
        else:
            level = "junior"

        if level != profile["inferred_level"]:
            with self.connection() as conn:
                conn.execute(
                    "UPDATE developer_profile SET inferred_level = ?, updated_at = ? WHERE profile_key = ?",
                    (level, utc_now(), profile_key),
                )

        return {
            "level": level,
            "score": score,
            "profile": {**profile, "inferred_level": level},
        }

    def get_developer_level(self, profile_key: str = "default") -> str:
        profile = self.get_developer_profile(profile_key)
        if not profile:
            return "junior"
        return profile["inferred_level"]

    def export_json(self, output_path: Path) -> None:
        payload: dict[str, list[dict]] = {}
        with self.connection() as conn:
            for table in (
                "inbox_items", "tasks", "memory_items", "artifacts", "project_links",
                "clarification_events", "sessions", "topic_keys", "topic_links",
                "model_contributions", "url_metadata", "external_references", "skill_references", "projects",
                "project_improvements", "developer_profile", "developer_interactions",
        ):
                rows = conn.execute(f"SELECT * FROM {table} ORDER BY id ASC").fetchall()
                payload[table] = [dict(row) for row in rows]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")

