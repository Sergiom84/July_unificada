from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from july.config import LLMSettings, Settings, UISettings
from july.db import JulyDatabase
from july.repositories.memory_repository import MemoryRepository
from july.storage.utils import utc_now


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


class MemoryRepositoryReadTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = JulyDatabase(build_test_settings(Path(self.temp_dir.name) / "july-test.db"))

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_database_delegates_read_methods_to_repository(self) -> None:
        self.assertIsInstance(self.database.memory, MemoryRepository)

    def test_read_methods_keep_existing_shapes(self) -> None:
        timestamp = utc_now()
        with self.database.connection() as conn:
            inbox_cursor = conn.execute(
                """
                INSERT INTO inbox_items (
                    raw_input, source_channel, detected_intent, intent_confidence,
                    status, normalized_summary, domain, project_key, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "Guardar decision",
                    "test",
                    "general_note",
                    0.9,
                    "captured",
                    "Guardar decision",
                    "tests",
                    "dashboard-av",
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
                (
                    inbox_cursor.lastrowid,
                    "follow_up",
                    "pending",
                    "Tarea derivada",
                    "dashboard-av",
                    timestamp,
                    timestamp,
                ),
            )
            conn.execute(
                """
                INSERT INTO memory_items (
                    inbox_item_id, memory_kind, title, summary, distilled_knowledge, domain,
                    scope, project_key, importance, confidence, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    inbox_cursor.lastrowid,
                    "decision",
                    "Decision de prueba",
                    "Resumen",
                    "Conocimiento",
                    "tests",
                    "project",
                    "dashboard-av",
                    3,
                    0.9,
                    "candidate",
                    timestamp,
                    timestamp,
                ),
            )

        inbox = self.database.list_inbox()
        tasks = self.database.list_tasks(status="pending")
        memory = self.database.list_memory()
        record = self.database.get_record("inbox_items", inbox[0]["id"])

        self.assertEqual(inbox[0]["normalized_summary"], "Guardar decision")
        self.assertEqual(tasks[0]["title"], "Tarea derivada")
        self.assertEqual(memory[0]["title"], "Decision de prueba")
        self.assertEqual(record["project_key"], "dashboard-av")

    def test_get_record_rejects_unsupported_tables(self) -> None:
        with self.assertRaises(ValueError):
            self.database.get_record("sqlite_master", 1)


if __name__ == "__main__":
    unittest.main()
