from __future__ import annotations

import sqlite3


def run_migrations(conn: sqlite3.Connection) -> None:
    """Apply compatibility migrations for databases created by older July versions."""
    migrate_projects_profile_columns(conn)
    migrate_nullable_task_inbox_item(conn)
    migrate_project_distillations(conn)
    migrate_sessions_updated_at(conn)


def migrate_projects_profile_columns(conn: sqlite3.Connection) -> None:
    project_column_names = table_column_names(conn, "projects")
    if "project_kind" not in project_column_names:
        conn.execute("ALTER TABLE projects ADD COLUMN project_kind TEXT NOT NULL DEFAULT 'unknown'")
    if "project_tags_json" not in project_column_names:
        conn.execute("ALTER TABLE projects ADD COLUMN project_tags_json TEXT NOT NULL DEFAULT '[]'")
    if "preferences_json" not in project_column_names:
        conn.execute("ALTER TABLE projects ADD COLUMN preferences_json TEXT NOT NULL DEFAULT '{}'")


def migrate_nullable_task_inbox_item(conn: sqlite3.Connection) -> None:
    task_columns = table_columns(conn, "tasks")
    inbox_item_column = next((row for row in task_columns if row["name"] == "inbox_item_id"), None)
    if not inbox_item_column or not inbox_item_column["notnull"]:
        return

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


def migrate_project_distillations(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS project_distillations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_key TEXT NOT NULL,
            from_session_id INTEGER,
            to_session_id INTEGER,
            session_count INTEGER NOT NULL DEFAULT 0,
            wiki_pages_changed_json TEXT NOT NULL DEFAULT '[]',
            notes TEXT,
            distilled_at TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_project_distillations_project_session
        ON project_distillations(project_key, to_session_id, distilled_at);
        """
    )


def migrate_sessions_updated_at(conn: sqlite3.Connection) -> None:
    session_column_names = table_column_names(conn, "sessions")
    if not session_column_names or "updated_at" in session_column_names:
        return
    conn.execute("ALTER TABLE sessions ADD COLUMN updated_at TEXT")
    conn.execute(
        """
        UPDATE sessions
        SET updated_at = COALESCE(started_at, ended_at, datetime('now'))
        WHERE updated_at IS NULL OR TRIM(updated_at) = ''
        """
    )


def table_columns(conn: sqlite3.Connection, table_name: str) -> list[sqlite3.Row]:
    return conn.execute(f"PRAGMA table_info({table_name})").fetchall()


def table_column_names(conn: sqlite3.Connection, table_name: str) -> set[str]:
    return {row["name"] for row in table_columns(conn, table_name)}
