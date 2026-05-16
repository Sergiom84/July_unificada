from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from july.config import LLMSettings, Settings, UISettings
from july.db import JulyDatabase
from july.repositories.task_repository import TaskRepository


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


class TaskRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = JulyDatabase(build_test_settings(Path(self.temp_dir.name) / "july-test.db"))

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_database_delegates_task_methods_to_repository(self) -> None:
        self.assertIsInstance(self.database.tasks, TaskRepository)

        created = self.database.create_manual_task(
            "dashboard-av",
            "Revisar pendientes",
            details="Validar la vista del cockpit",
        )
        updated = self.database.update_task_status(created["id"], "in_progress", project_key="dashboard-av")
        listed = self.database.list_project_tasks("dashboard-av")

        self.assertEqual(created["task_type"], "manual_follow_up")
        self.assertEqual(updated["status"], "in_progress")
        self.assertEqual([row["id"] for row in listed], [created["id"]])

    def test_improvements_preserve_filters_order_and_closed_status(self) -> None:
        low = self.database.create_project_improvement("dashboard-av", "Mejora baja", priority="low")
        high = self.database.create_project_improvement("dashboard-av", "Mejora alta", priority="high")
        done = self.database.create_project_improvement("dashboard-av", "Mejora hecha")

        closed = self.database.update_project_improvement_status(done["id"], "done", project_key="dashboard-av")
        active = self.database.list_project_improvements("dashboard-av")
        all_items = self.database.list_project_improvements("dashboard-av", include_closed=True)

        self.assertEqual(closed["status"], "done")
        self.assertIsNotNone(closed["closed_at"])
        self.assertEqual([row["id"] for row in active], [high["id"], low["id"]])
        self.assertEqual({row["id"] for row in all_items}, {low["id"], high["id"], done["id"]})

    def test_invalid_statuses_are_rejected(self) -> None:
        task = self.database.create_manual_task("dashboard-av", "Pendiente")
        improvement = self.database.create_project_improvement("dashboard-av", "Mejora")

        with self.assertRaises(ValueError):
            self.database.create_manual_task("dashboard-av", "Rota", status="blocked")
        with self.assertRaises(ValueError):
            self.database.update_task_status(task["id"], "blocked", project_key="dashboard-av")
        with self.assertRaises(ValueError):
            self.database.create_project_improvement("dashboard-av", "Rota", priority="urgent")
        with self.assertRaises(ValueError):
            self.database.update_project_improvement_status(improvement["id"], "blocked", project_key="dashboard-av")


if __name__ == "__main__":
    unittest.main()
