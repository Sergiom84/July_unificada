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

    def test_capture_promote_and_resolve_clarification_delegate_to_repository(self) -> None:
        first = self.database.capture(
            "Guardar decision inicial",
            "test",
            None,
            build_plan(
                status="needs_clarification",
                clarification_question="¿Qué proyecto?",
                task_title="Tarea inicial",
                memory_title="Memoria inicial",
            ),
        )

        promoted = self.database.promote_memory(
            first["memory_item_id"],
            title="Memoria lista",
            distilled_knowledge="Conocimiento listo",
        )
        resolved = self.database.resolve_clarification(
            first["inbox_item_id"],
            "Es para dashboard-av",
            build_plan(
                status="captured",
                task_title="Tarea final",
                memory_title="Memoria final",
            ),
        )

        inbox = self.database.get_record("inbox_items", first["inbox_item_id"])
        tasks = self.database.list_tasks()
        memory = self.database.list_memory()
        clarification = self.database.get_record("clarification_events", 1)

        self.assertEqual(promoted["title"], "Memoria lista")
        self.assertEqual(inbox["status"], "captured")
        self.assertEqual(resolved["inbox_item_id"], first["inbox_item_id"])
        self.assertEqual(tasks[0]["title"], "Tarea final")
        self.assertEqual(memory[0]["title"], "Memoria final")
        self.assertEqual(clarification["answer"], "Es para dashboard-av")
        self.assertEqual(len(tasks), 1)
        self.assertEqual(len(memory), 1)


def build_plan(
    *,
    status: str,
    clarification_question: str | None = None,
    task_title: str,
    memory_title: str,
) -> dict:
    return {
        "classification": {
            "intent": "general_note",
            "confidence": 0.9,
            "status": status,
            "clarification_question": clarification_question,
            "normalized_summary": memory_title,
            "domain": "tests",
            "project_key": "dashboard-av",
        },
        "task": {
            "task_type": "follow_up",
            "status": "pending",
            "title": task_title,
            "details": f"Detalle de {task_title}",
            "project_key": "dashboard-av",
            "due_hint": None,
        },
        "memory": {
            "memory_kind": "decision",
            "title": memory_title,
            "summary": f"Resumen de {memory_title}",
            "distilled_knowledge": f"Conocimiento de {memory_title}",
            "domain": "tests",
            "scope": "project",
            "project_key": "dashboard-av",
            "importance": 3,
            "confidence": 0.9,
            "status": "candidate",
        },
        "artifacts": [
            {
                "artifact_type": "path",
                "value": "README.md",
                "metadata_json": "{}",
            }
        ],
        "context": {
            "project_keys": ["dashboard-av"],
        },
    }


if __name__ == "__main__":
    unittest.main()
