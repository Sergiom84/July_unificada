from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from july.config import LLMSettings, Settings, UISettings
from july.db import JulyDatabase


def build_test_settings(db_path: Path) -> Settings:
    return Settings(
        db_path=db_path,
        llm=LLMSettings(
            provider="none",
            model=None,
            api_key=None,
            base_url=None,
            timeout_seconds=30,
        ),
        ui=UISettings(
            host="127.0.0.1",
            port=4317,
            base_url=None,
        ),
    )


class StorageMigrationTests(unittest.TestCase):
    def test_legacy_schema_is_migrated_on_database_init(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "legacy.db"
            create_legacy_database(db_path)

            database = JulyDatabase(build_test_settings(db_path))

            project = database.get_project("legacy-project")
            task = database.get_record("tasks", 1)
            with database.connection() as conn:
                task_columns = {row["name"]: row for row in conn.execute("PRAGMA table_info(tasks)").fetchall()}
                session_columns = {row["name"] for row in conn.execute("PRAGMA table_info(sessions)").fetchall()}
                distillation_columns = {
                    row["name"] for row in conn.execute("PRAGMA table_info(project_distillations)").fetchall()
                }
                audit_columns = {
                    row["name"] for row in conn.execute("PRAGMA table_info(memory_audit_findings)").fetchall()
                }
                legacy_session = conn.execute("SELECT * FROM sessions WHERE session_key = ?", ("legacy-session",)).fetchone()

            self.assertIsNotNone(project)
            self.assertEqual(project["project_kind"], "unknown")
            self.assertEqual(project["project_tags_json"], "[]")
            self.assertEqual(project["preferences_json"], "{}")
            self.assertEqual(task["title"], "Legacy task")
            self.assertEqual(task_columns["inbox_item_id"]["notnull"], 0)
            self.assertIn("updated_at", session_columns)
            self.assertEqual(legacy_session["updated_at"], "2026-05-16T00:00:00+00:00")
            self.assertIn("wiki_pages_changed_json", distillation_columns)
            self.assertIn("evidence_json", audit_columns)


def create_legacy_database(db_path: Path) -> None:
    timestamp = "2026-05-16T00:00:00+00:00"
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(
            """
            CREATE TABLE inbox_items (
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

            CREATE TABLE tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inbox_item_id INTEGER NOT NULL REFERENCES inbox_items(id) ON DELETE CASCADE,
                task_type TEXT NOT NULL,
                status TEXT NOT NULL,
                title TEXT NOT NULL,
                details TEXT,
                project_key TEXT,
                due_hint TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_key TEXT NOT NULL UNIQUE,
                repo_root TEXT NOT NULL,
                repo_name TEXT NOT NULL,
                display_name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL
            );

            CREATE TABLE sessions (
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
            """
        )
        conn.execute(
            """
            INSERT INTO inbox_items (
                raw_input, source_channel, detected_intent, intent_confidence,
                status, normalized_summary, domain, project_key, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "Legacy input",
                "test",
                "general_note",
                0.9,
                "captured",
                "Legacy input",
                "tests",
                "legacy-project",
                timestamp,
                timestamp,
            ),
        )
        conn.execute(
            """
            INSERT INTO tasks (
                inbox_item_id, task_type, status, title, project_key, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (1, "follow_up", "pending", "Legacy task", "legacy-project", timestamp, timestamp),
        )
        conn.execute(
            """
            INSERT INTO projects (
                project_key, repo_root, repo_name, display_name, created_at, updated_at, last_seen_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "legacy-project",
                str(db_path.parent / "Legacy"),
                "Legacy",
                "Legacy",
                timestamp,
                timestamp,
                timestamp,
            ),
        )
        conn.execute(
            """
            INSERT INTO sessions (
                session_key, project_key, agent_name, goal, status, started_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("legacy-session", "legacy-project", "codex", "Legacy work", "active", timestamp),
        )
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    unittest.main()
