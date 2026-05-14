from __future__ import annotations

import json
import re
import sqlite3
import unicodedata
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from july.config import Settings

IMPROVEMENT_STATUSES = {"open", "planned", "in_progress", "done", "dismissed"}
ACTIVE_IMPROVEMENT_STATUSES = ("open", "planned", "in_progress")
IMPROVEMENT_PRIORITIES = {"low", "normal", "high"}
TASK_STATUSES = {"pending", "in_progress", "done"}
SKILL_REFERENCE_STATUSES = {"active", "inactive"}
SKILL_STOPWORDS = {
    "con", "del", "las", "los", "para", "por", "que", "una", "unos", "unas",
    "and", "the", "when", "use", "using", "user", "from", "this", "that",
    "como", "cuando", "donde", "este", "esta", "estos", "estas", "algo",
    "antes", "despues", "sobre", "tiene", "tener", "hacer", "hace", "hacia",
    "hacia", "hacía", "quiero", "necesito", "cual", "cuál", "era", "sirve",
    "ayuda", "ayudar", "alguna", "alguno", "tenemos", "skill", "skills",
    "proyecto", "proyectos", "crear", "crea",
}

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS inbox_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_input TEXT NOT NULL,
    source_channel TEXT NOT NULL,
    source_ref TEXT,
    detected_intent TEXT NOT NULL,
    intent_confidence REAL NOT NULL,
    status TEXT NOT NULL,
    clarification_question TEXT,
    normalized_summary TEXT NOT NULL,
    domain TEXT NOT NULL,
    project_key TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
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

CREATE TABLE IF NOT EXISTS memory_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inbox_item_id INTEGER REFERENCES inbox_items(id) ON DELETE SET NULL,
    memory_kind TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    distilled_knowledge TEXT NOT NULL,
    domain TEXT NOT NULL,
    scope TEXT NOT NULL,
    project_key TEXT,
    importance INTEGER NOT NULL,
    confidence REAL NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS artifacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inbox_item_id INTEGER NOT NULL REFERENCES inbox_items(id) ON DELETE CASCADE,
    artifact_type TEXT NOT NULL,
    value TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS project_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inbox_item_id INTEGER REFERENCES inbox_items(id) ON DELETE CASCADE,
    memory_item_id INTEGER REFERENCES memory_items(id) ON DELETE CASCADE,
    project_key TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    confidence REAL NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_key TEXT NOT NULL UNIQUE,
    repo_root TEXT NOT NULL,
    repo_name TEXT NOT NULL,
    display_name TEXT NOT NULL,
    project_kind TEXT NOT NULL DEFAULT 'unknown',
    project_tags_json TEXT NOT NULL DEFAULT '[]',
    preferences_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS project_improvements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_key TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'open',
    priority TEXT NOT NULL DEFAULT 'normal',
    source_channel TEXT NOT NULL DEFAULT 'cli',
    source_ref TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    closed_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_project_improvements_project_status
ON project_improvements(project_key, status, updated_at);

CREATE TABLE IF NOT EXISTS clarification_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inbox_item_id INTEGER NOT NULL REFERENCES inbox_items(id) ON DELETE CASCADE,
    question TEXT,
    answer TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_key TEXT NOT NULL UNIQUE,
    project_key TEXT,
    agent_name TEXT,
    goal TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    summary TEXT,
    discoveries TEXT,
    accomplished TEXT,
    next_steps TEXT,
    relevant_files TEXT,
    started_at TEXT NOT NULL,
    ended_at TEXT
);

CREATE TABLE IF NOT EXISTS topic_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_key TEXT NOT NULL UNIQUE,
    label TEXT NOT NULL,
    domain TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS topic_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_key_id INTEGER NOT NULL REFERENCES topic_keys(id) ON DELETE CASCADE,
    inbox_item_id INTEGER REFERENCES inbox_items(id) ON DELETE SET NULL,
    memory_item_id INTEGER REFERENCES memory_items(id) ON DELETE SET NULL,
    session_id INTEGER REFERENCES sessions(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS model_contributions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT NOT NULL,
    contribution_type TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    inbox_item_id INTEGER REFERENCES inbox_items(id) ON DELETE SET NULL,
    memory_item_id INTEGER REFERENCES memory_items(id) ON DELETE SET NULL,
    session_id INTEGER REFERENCES sessions(id) ON DELETE SET NULL,
    project_key TEXT,
    domain TEXT,
    adopted INTEGER NOT NULL DEFAULT 0,
    notes TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS url_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    artifact_id INTEGER REFERENCES artifacts(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    resolved_title TEXT,
    description TEXT,
    content_type TEXT,
    extracted_text TEXT,
    youtube_video_id TEXT,
    youtube_channel TEXT,
    youtube_duration TEXT,
    fetch_status TEXT NOT NULL DEFAULT 'pending',
    fetched_at TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS external_references (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_url TEXT NOT NULL,
    source_name TEXT NOT NULL,
    reference_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    relevance_note TEXT,
    inbox_item_id INTEGER REFERENCES inbox_items(id) ON DELETE SET NULL,
    memory_item_id INTEGER REFERENCES memory_items(id) ON DELETE SET NULL,
    project_key TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS skill_references (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_name TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    source_path TEXT,
    trigger_text TEXT NOT NULL,
    domains_json TEXT NOT NULL DEFAULT '[]',
    project_keys_json TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_skill_references_status
ON skill_references(status, updated_at);

CREATE TABLE IF NOT EXISTS developer_profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_key TEXT NOT NULL UNIQUE DEFAULT 'default',
    inferred_level TEXT NOT NULL DEFAULT 'junior',
    total_interactions INTEGER NOT NULL DEFAULT 0,
    decisions_count INTEGER NOT NULL DEFAULT 0,
    architecture_questions INTEGER NOT NULL DEFAULT 0,
    code_smells_addressed INTEGER NOT NULL DEFAULT 0,
    patterns_applied INTEGER NOT NULL DEFAULT 0,
    last_interaction_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS developer_interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_key TEXT NOT NULL DEFAULT 'default',
    interaction_type TEXT NOT NULL,
    complexity TEXT NOT NULL DEFAULT 'basic',
    project_key TEXT,
    detail TEXT,
    created_at TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS inbox_items_fts USING fts5(
    raw_input,
    normalized_summary,
    content='inbox_items',
    content_rowid='id'
);

CREATE VIRTUAL TABLE IF NOT EXISTS memory_items_fts USING fts5(
    title,
    summary,
    distilled_knowledge,
    content='memory_items',
    content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS inbox_items_ai AFTER INSERT ON inbox_items BEGIN
    INSERT INTO inbox_items_fts(rowid, raw_input, normalized_summary)
    VALUES (new.id, new.raw_input, new.normalized_summary);
END;

CREATE TRIGGER IF NOT EXISTS inbox_items_ad AFTER DELETE ON inbox_items BEGIN
    INSERT INTO inbox_items_fts(inbox_items_fts, rowid, raw_input, normalized_summary)
    VALUES ('delete', old.id, old.raw_input, old.normalized_summary);
END;

CREATE TRIGGER IF NOT EXISTS inbox_items_au AFTER UPDATE ON inbox_items BEGIN
    INSERT INTO inbox_items_fts(inbox_items_fts, rowid, raw_input, normalized_summary)
    VALUES ('delete', old.id, old.raw_input, old.normalized_summary);
    INSERT INTO inbox_items_fts(rowid, raw_input, normalized_summary)
    VALUES (new.id, new.raw_input, new.normalized_summary);
END;

CREATE TRIGGER IF NOT EXISTS memory_items_ai AFTER INSERT ON memory_items BEGIN
    INSERT INTO memory_items_fts(rowid, title, summary, distilled_knowledge)
    VALUES (new.id, new.title, new.summary, new.distilled_knowledge);
END;

CREATE TRIGGER IF NOT EXISTS memory_items_ad AFTER DELETE ON memory_items BEGIN
    INSERT INTO memory_items_fts(memory_items_fts, rowid, title, summary, distilled_knowledge)
    VALUES ('delete', old.id, old.title, old.summary, old.distilled_knowledge);
END;

CREATE TRIGGER IF NOT EXISTS memory_items_au AFTER UPDATE ON memory_items BEGIN
    INSERT INTO memory_items_fts(memory_items_fts, rowid, title, summary, distilled_knowledge)
    VALUES ('delete', old.id, old.title, old.summary, old.distilled_knowledge);
    INSERT INTO memory_items_fts(rowid, title, summary, distilled_knowledge)
    VALUES (new.id, new.title, new.summary, new.distilled_knowledge);
END;
"""


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def normalize_json_array(values: list[str] | tuple[str, ...] | None) -> list[str]:
    if not values:
        return []
    normalized = []
    for value in values:
        item = str(value).strip()
        if item and item not in normalized:
            normalized.append(item)
    return normalized


def parse_json_array(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed if str(item).strip()]


def skill_reference_tokens(text: str) -> set[str]:
    normalized = unicodedata.normalize("NFKD", text.lower())
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return {
        token for token in re.findall(r"[a-z0-9][a-z0-9_/-]{2,}", normalized)
        if token not in SKILL_STOPWORDS
    }


class JulyDatabase:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.settings.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

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

    # ── Session protocol ──────────────────────────────────────────────

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
                INSERT INTO sessions (session_key, project_key, agent_name, goal, status, started_at)
                VALUES (?, ?, ?, ?, 'active', ?)
                """,
                (session_key, project_key, agent_name, goal, timestamp),
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
                    next_steps = ?, relevant_files = ?, status = 'summarized'
                WHERE session_key = ?
                """,
                (summary, discoveries, accomplished, next_steps, relevant_files, session_key),
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
                    ended_at = COALESCE(ended_at, ?)
                WHERE session_key = ?
                """,
                (timestamp, session_key),
            )
            updated = conn.execute(
                "SELECT status, ended_at FROM sessions WHERE session_key = ?",
                (session_key,),
            ).fetchone()
        return {
            "session_key": session_key,
            "status": updated["status"],
            "ended_at": updated["ended_at"],
        }

    def session_context(self, project_key: str | None = None, limit: int = 5) -> list[dict]:
        with self.connection() as conn:
            if project_key:
                rows = conn.execute(
                    """
                    SELECT id, session_key, project_key, agent_name, goal, status,
                           summary, discoveries, next_steps, started_at, ended_at
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
                           summary, discoveries, next_steps, started_at, ended_at
                    FROM sessions
                    ORDER BY id DESC LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
        return [dict(r) for r in rows]

    def get_open_session(self, project_key: str) -> dict | None:
        with self.connection() as conn:
            row = conn.execute(
                """
                SELECT id, session_key, project_key, agent_name, goal, status,
                       summary, discoveries, accomplished, next_steps, relevant_files,
                       started_at, ended_at
                FROM sessions
                WHERE project_key = ? AND ended_at IS NULL AND status IN ('active', 'summarized')
                ORDER BY id DESC
                LIMIT 1
                """,
                (project_key,),
            ).fetchone()
        return dict(row) if row is not None else None

    def list_sessions(self, status: str | None = None, limit: int = 20) -> list[sqlite3.Row]:
        query = """
            SELECT id, session_key, project_key, agent_name, goal, status, started_at, ended_at
            FROM sessions
        """
        params: list[object] = []
        if status:
            query += " WHERE status = ?"
            params.append(status)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        with self.connection() as conn:
            return conn.execute(query, tuple(params)).fetchall()

    # ── Topic keys ────────────────────────────────────────────────────

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
            memory_ids = [l["memory_item_id"] for l in links if l["memory_item_id"]]
            memories = []
            for mid in memory_ids:
                row = conn.execute(
                    "SELECT id, memory_kind, status, title, summary, domain, scope, project_key FROM memory_items WHERE id = ?",
                    (mid,),
                ).fetchone()
                if row:
                    memories.append(dict(row))
        return {"topic": dict(topic), "links": [dict(l) for l in links], "memories": memories}

    def list_topics(self, limit: int = 50) -> list[sqlite3.Row]:
        with self.connection() as conn:
            return conn.execute(
                "SELECT id, topic_key, label, domain, description, created_at FROM topic_keys ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()

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

    def upsert_skill_reference(
        self,
        *,
        skill_name: str,
        description: str,
        source_path: str | None = None,
        trigger_text: str | None = None,
        display_name: str | None = None,
        domains: list[str] | tuple[str, ...] | None = None,
        project_keys: list[str] | tuple[str, ...] | None = None,
        status: str = "active",
    ) -> dict:
        skill_name = skill_name.strip()
        description = description.strip()
        trigger_text = (trigger_text or description).strip()
        display_name = (display_name or skill_name).strip()
        if not skill_name:
            raise ValueError("skill_name is required")
        if not description:
            raise ValueError("description is required")
        if status not in SKILL_REFERENCE_STATUSES:
            raise ValueError(f"Unsupported skill reference status: {status}")

        timestamp = utc_now()
        domains_json = json.dumps(normalize_json_array(domains), ensure_ascii=True)
        project_keys_json = json.dumps(normalize_json_array(project_keys), ensure_ascii=True)
        with self.connection() as conn:
            existing = conn.execute(
                "SELECT id FROM skill_references WHERE skill_name = ?",
                (skill_name,),
            ).fetchone()
            if existing:
                conn.execute(
                    """
                    UPDATE skill_references
                    SET display_name = ?, description = ?, source_path = ?, trigger_text = ?,
                        domains_json = ?, project_keys_json = ?, status = ?, updated_at = ?
                    WHERE skill_name = ?
                    """,
                    (
                        display_name, description, source_path, trigger_text,
                        domains_json, project_keys_json, status, timestamp, skill_name,
                    ),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO skill_references (
                        skill_name, display_name, description, source_path, trigger_text,
                        domains_json, project_keys_json, status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        skill_name, display_name, description, source_path, trigger_text,
                        domains_json, project_keys_json, status, timestamp, timestamp,
                    ),
                )
            row = conn.execute(
                "SELECT * FROM skill_references WHERE skill_name = ?",
                (skill_name,),
            ).fetchone()
            return dict(row)

    def list_skill_references(
        self,
        *,
        status: str | None = "active",
        include_inactive: bool = False,
        include_trigger: bool = False,
        limit: int = 20,
    ) -> list[sqlite3.Row]:
        if status and status not in SKILL_REFERENCE_STATUSES:
            raise ValueError(f"Unsupported skill reference status: {status}")
        columns = (
            "id, skill_name, display_name, description, source_path, "
            f"{'trigger_text, ' if include_trigger else ''}"
            "domains_json, project_keys_json, status, created_at, updated_at"
        )
        with self.connection() as conn:
            if include_inactive:
                return conn.execute(
                    f"""
                    SELECT {columns}
                    FROM skill_references
                    ORDER BY updated_at DESC, id DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
            return conn.execute(
                f"""
                SELECT {columns}
                FROM skill_references
                WHERE status = ?
                ORDER BY updated_at DESC, id DESC
                LIMIT ?
                """,
                (status or "active", limit),
            ).fetchall()

    def suggest_skill_references(
        self,
        text: str,
        *,
        project_key: str | None = None,
        limit: int = 5,
    ) -> list[dict]:
        query_tokens = skill_reference_tokens(text)
        if not query_tokens:
            return []

        suggestions: list[dict] = []
        for row in self.list_skill_references(limit=200, include_trigger=True):
            item = dict(row)
            domains = parse_json_array(item.get("domains_json"))
            project_keys = parse_json_array(item.get("project_keys_json"))
            haystack = " ".join(
                [
                    item["skill_name"],
                    item["display_name"],
                    item["description"],
                    item.get("source_path") or "",
                    " ".join(domains),
                ]
            )
            haystack = f"{haystack} {item.get('trigger_text') or ''}"

            skill_tokens = skill_reference_tokens(haystack)
            overlap = sorted(query_tokens & skill_tokens)
            domain_hits = sorted(query_tokens & skill_reference_tokens(" ".join(domains)))
            project_match = bool(project_key and project_key in project_keys)
            if not overlap and not project_match:
                continue

            score = (len(overlap) * 2) + (len(domain_hits) * 3)
            if project_match:
                score += 8
            elif project_keys:
                score -= 1
            else:
                score += 1

            if score <= 3:
                continue

            if project_match:
                reason = f"Registrada para este proyecto; coincide con: {', '.join(overlap[:5]) or project_key}"
            elif domain_hits:
                reason = f"Coincide con dominios: {', '.join(domain_hits[:5])}"
            else:
                reason = f"Coincide con: {', '.join(overlap[:5])}"

            suggestions.append({
                "type": "skill_reference",
                "skill_name": item["skill_name"],
                "display_name": item["display_name"],
                "description": item["description"],
                "source_path": item.get("source_path"),
                "domains": domains,
                "project_keys": project_keys,
                "score": score,
                "reason": reason,
            })

        suggestions.sort(key=lambda suggestion: suggestion["score"], reverse=True)
        return suggestions[:limit]

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
