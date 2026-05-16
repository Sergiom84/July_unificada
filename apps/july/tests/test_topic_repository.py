from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from july.config import LLMSettings, Settings, UISettings
from july.db import JulyDatabase
from july.repositories.topic_repository import TopicRepository
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


class TopicRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = JulyDatabase(build_test_settings(Path(self.temp_dir.name) / "july-test.db"))

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_database_delegates_topic_methods_to_repository(self) -> None:
        self.assertIsInstance(self.database.topics, TopicRepository)

    def test_create_topic_is_idempotent_and_lists_topics(self) -> None:
        created = self.database.create_topic("auth/jwt-flow", "Autenticación JWT", "backend", "Flujo JWT")
        duplicate = self.database.create_topic("auth/jwt-flow", "Autenticación JWT", "backend")
        topics = self.database.list_topics()

        self.assertEqual(created["status"], "created")
        self.assertEqual(duplicate["status"], "already_exists")
        self.assertEqual(duplicate["topic_id"], created["topic_id"])
        self.assertEqual(topics[0]["topic_key"], "auth/jwt-flow")

    def test_link_to_topic_and_context_include_memory(self) -> None:
        self.database.create_topic("auth/jwt-flow", "Autenticación JWT", "backend")
        memory_id = self._insert_memory("JWT decidido")

        link = self.database.link_to_topic("auth/jwt-flow", memory_item_id=memory_id)
        context = self.database.topic_context("auth/jwt-flow")

        self.assertTrue(link["linked"])
        self.assertEqual(context["topic"]["topic_key"], "auth/jwt-flow")
        self.assertEqual(context["links"][0]["memory_item_id"], memory_id)
        self.assertEqual(context["memories"][0]["title"], "JWT decidido")

    def test_missing_topic_errors_are_preserved(self) -> None:
        with self.assertRaises(ValueError):
            self.database.link_to_topic("missing/topic", memory_item_id=1)
        with self.assertRaises(ValueError):
            self.database.topic_context("missing/topic")

    def _insert_memory(self, title: str) -> int:
        timestamp = utc_now()
        with self.database.connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO memory_items (
                    memory_kind, title, summary, distilled_knowledge, domain, scope,
                    project_key, importance, confidence, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "decision",
                    title,
                    "Resumen",
                    "Conocimiento",
                    "backend",
                    "project",
                    "dashboard-av",
                    3,
                    0.9,
                    "ready",
                    timestamp,
                    timestamp,
                ),
            )
        return cursor.lastrowid


if __name__ == "__main__":
    unittest.main()
