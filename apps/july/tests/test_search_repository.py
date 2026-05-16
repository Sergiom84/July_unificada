from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from july.config import LLMSettings, Settings, UISettings
from july.db import JulyDatabase
from july.repositories.search_repository import SearchRepository
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


class SearchRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = JulyDatabase(build_test_settings(Path(self.temp_dir.name) / "july-test.db"))

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_database_delegates_search_methods_to_repository(self) -> None:
        self.assertIsInstance(self.database.searches, SearchRepository)

    def test_search_keeps_existing_result_shape(self) -> None:
        self._insert_search_fixture()

        result = self.database.search("JWT")

        self.assertEqual(result["inbox"][0]["normalized_summary"], "JWT auth")
        self.assertEqual(result["memory"][0]["title"], "JWT decision")
        self.assertEqual(result["tasks"][0]["title"], "Revisar JWT")
        self.assertEqual(result["improvements"][0]["title"], "Mejorar JWT")

    def test_proactive_recall_returns_memory_sessions_and_skill_suggestions(self) -> None:
        self._insert_search_fixture(memory_scope="global")
        self.database.session_start("ses-jwt", project_key="dashboard-av", goal="JWT auth")
        self.database.session_summary("ses-jwt", summary="Resumen JWT", next_steps="Seguir con refresh")
        self.database.upsert_skill_reference(
            skill_name="entrevistador-procesos",
            display_name="Entrevistador procesos",
            description="Define procesos, workflows y automatizaciones ambiguas antes de construir.",
            domains=["procesos", "workflow", "automatizacion"],
        )

        recall = self.database.proactive_recall(
            "Necesito definir una automatizacion con tokens JWT",
            project_key="dashboard-av",
        )

        self.assertEqual(recall["related_memories"][0]["title"], "JWT decision")
        self.assertEqual(recall["related_sessions"][0]["session_key"], "ses-jwt")
        self.assertEqual(recall["suggestions"][0]["type"], "reuse_memory")
        self.assertEqual(recall["skill_suggestions"][0]["skill_name"], "entrevistador-procesos")

    def _insert_search_fixture(self, *, memory_scope: str = "project") -> None:
        timestamp = utc_now()
        with self.database.connection() as conn:
            inbox = conn.execute(
                """
                INSERT INTO inbox_items (
                    raw_input, source_channel, detected_intent, intent_confidence,
                    status, normalized_summary, domain, project_key, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "JWT auth",
                    "test",
                    "general_note",
                    0.9,
                    "captured",
                    "JWT auth",
                    "backend",
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
                    inbox.lastrowid,
                    "decision",
                    "JWT decision",
                    "Resumen JWT",
                    "Usar JWT con refresh tokens",
                    "backend",
                    memory_scope,
                    "dashboard-av",
                    5,
                    0.9,
                    "ready",
                    timestamp,
                    timestamp,
                ),
            )
            conn.execute(
                """
                INSERT INTO tasks (
                    inbox_item_id, task_type, status, title, details, project_key,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    inbox.lastrowid,
                    "follow_up",
                    "pending",
                    "Revisar JWT",
                    "Detalles JWT",
                    "dashboard-av",
                    timestamp,
                    timestamp,
                ),
            )
            conn.execute(
                """
                INSERT INTO project_improvements (
                    project_key, title, description, status, priority,
                    source_channel, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "dashboard-av",
                    "Mejorar JWT",
                    "Descripción JWT",
                    "open",
                    "normal",
                    "test",
                    timestamp,
                    timestamp,
                ),
            )


if __name__ == "__main__":
    unittest.main()
