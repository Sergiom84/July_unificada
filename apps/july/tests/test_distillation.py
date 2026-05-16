from __future__ import annotations

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


class ProjectDistillationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(self.temp_dir.name) / "july-test.db"
        self.database = JulyDatabase(build_test_settings(db_path))
        self.database.upsert_project("dashboard-av", str(Path(self.temp_dir.name) / "Dashboard_AV"))

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_closed_session_threshold_requests_distillation_and_record_resets_counter(self) -> None:
        for i in range(5):
            session_key = f"dashboard-session-{i}"
            self.database.session_start(session_key, project_key="dashboard-av")
            self.database.session_summary(session_key, summary=f"Resumen {i}")
            result = self.database.session_end(session_key)

        self.assertTrue(result["distillation"]["needs_distillation"])
        self.assertEqual(result["distillation"]["sessions_since_last"], 5)

        record = self.database.record_distillation(
            "dashboard-av",
            wiki_pages_changed=["context/wiki/concepts/dashboard-av.md"],
            notes="Destilado de prueba",
        )
        after = self.database.distill_candidates("dashboard-av")

        self.assertEqual(record["session_count"], 5)
        self.assertEqual(record["wiki_pages_changed"], ["context/wiki/concepts/dashboard-av.md"])
        self.assertFalse(after["needs_distillation"])
        self.assertEqual(after["sessions_since_last"], 0)

    def test_decision_memory_requests_distillation_before_threshold(self) -> None:
        with self.database.connection() as conn:
            conn.execute(
                """
                INSERT INTO memory_items (
                    memory_kind, title, summary, distilled_knowledge, domain, scope,
                    project_key, importance, confidence, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "procedural",
                    "Decision reutilizable: usar cockpit local",
                    "Decision: cockpit local para reducir ambiguedad.",
                    "Decision reutilizable para proyectos con memoria operativa.",
                    "Programacion",
                    "project",
                    "dashboard-av",
                    4,
                    0.95,
                    "ready",
                    "2026-05-16T00:00:00+00:00",
                    "2026-05-16T00:00:00+00:00",
                ),
            )

        result = self.database.distill_candidates("dashboard-av")

        self.assertTrue(result["needs_distillation"])
        self.assertEqual(result["candidate_counts"]["decisions"], 1)


if __name__ == "__main__":
    unittest.main()
