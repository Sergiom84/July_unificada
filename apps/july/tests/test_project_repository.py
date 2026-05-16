from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from july.config import LLMSettings, Settings, UISettings
from july.db import JulyDatabase
from july.repositories.project_repository import ProjectRepository
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


class ProjectRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.database = JulyDatabase(build_test_settings(self.root / "july-test.db"))

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_database_delegates_project_methods_to_repository(self) -> None:
        self.assertIsInstance(self.database.projects, ProjectRepository)

        created = self.database.upsert_project(
            "dashboard-av",
            str(self.root / "Dashboard_AV"),
            project_kind="web_app",
            project_tags=["web_app", "cliente"],
            preferences={"suggest_caveman": True},
        )
        updated = self.database.upsert_project("dashboard-av", str(self.root / "Dashboard_AV"))

        self.assertEqual(created["project_key"], "dashboard-av")
        self.assertEqual(updated["project_kind"], "web_app")
        self.assertEqual(json.loads(updated["project_tags_json"]), ["cliente", "web_app"])
        self.assertTrue(json.loads(updated["preferences_json"])["suggest_caveman"])

    def test_project_context_and_totals_keep_existing_shape(self) -> None:
        self.database.upsert_project("dashboard-av", str(self.root / "Dashboard_AV"))
        timestamp = utc_now()
        with self.database.connection() as conn:
            conn.execute(
                """
                INSERT INTO inbox_items (
                    raw_input, source_channel, detected_intent, intent_confidence,
                    status, normalized_summary, domain, project_key, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "Decision de prueba",
                    "test",
                    "general_note",
                    0.9,
                    "captured",
                    "Decision de prueba",
                    "tests",
                    "dashboard-av",
                    timestamp,
                    timestamp,
                ),
            )
            conn.execute(
                """
                INSERT INTO memory_items (
                    memory_kind, title, summary, distilled_knowledge, domain, scope,
                    project_key, importance, confidence, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "finding",
                    "Hallazgo: prueba",
                    "Resumen",
                    "Conocimiento destilado",
                    "tests",
                    "project",
                    "dashboard-av",
                    3,
                    0.9,
                    "ready",
                    timestamp,
                    timestamp,
                ),
            )
        self.database.create_manual_task("dashboard-av", "Tarea abierta")
        self.database.create_project_improvement("dashboard-av", "Mejora abierta", priority="high")
        done = self.database.create_project_improvement("dashboard-av", "Mejora cerrada")
        self.database.update_project_improvement_status(done["id"], "done", project_key="dashboard-av")

        context = self.database.project_context("dashboard-av")
        totals = self.database.get_project_totals("dashboard-av")
        projects = self.database.list_projects()

        self.assertEqual(len(context["inbox"]), 1)
        self.assertEqual(len(context["memory"]), 1)
        self.assertEqual(len(context["tasks"]), 1)
        self.assertEqual([row["title"] for row in context["improvements"]], ["Mejora abierta"])
        self.assertEqual(totals["memory_items"], 1)
        self.assertEqual(totals["findings"], 1)
        self.assertEqual(totals["pending_tasks"], 1)
        self.assertEqual(totals["open_improvements"], 1)
        self.assertEqual(projects[0]["open_improvements"], 1)


if __name__ == "__main__":
    unittest.main()
