from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from july.config import LLMSettings, Settings, UISettings
from july.db import JulyDatabase
from july.repositories.reference_repository import ReferenceRepository


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


class ReferenceRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = JulyDatabase(build_test_settings(Path(self.temp_dir.name) / "july-test.db"))

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_database_delegates_reference_methods_to_repository(self) -> None:
        self.assertIsInstance(self.database.references, ReferenceRepository)

    def test_model_contributions_can_be_listed_and_adopted(self) -> None:
        created = self.database.save_model_contribution(
            "codex",
            "architecture",
            "Propuesta de refactor",
            "Separar repositorios por dominio",
            project_key="july-unificada",
            domain="refactor",
        )
        adopted = self.database.adopt_contribution(created["contribution_id"], notes="Adoptada")
        listed = self.database.list_model_contributions(model_name="codex", project_key="july-unificada")

        self.assertEqual(created["model_name"], "codex")
        self.assertTrue(adopted["adopted"])
        self.assertEqual(listed[0]["title"], "Propuesta de refactor")
        self.assertEqual(listed[0]["adopted"], 1)

    def test_url_metadata_returns_latest_row_for_url(self) -> None:
        self.database.save_url_metadata("https://example.com", resolved_title="Primera")
        latest = self.database.save_url_metadata("https://example.com", resolved_title="Última", fetch_status="cached")
        row = self.database.get_url_metadata("https://example.com")

        self.assertEqual(latest["fetch_status"], "cached")
        self.assertEqual(row["resolved_title"], "Última")

    def test_external_references_can_be_filtered_by_project(self) -> None:
        self.database.save_external_reference(
            "https://agents.md",
            "agents.md",
            "agent_pattern",
            "Patrones de agentes",
            relevance_note="Útil para MCP",
            project_key="july-unificada",
        )
        self.database.save_external_reference(
            "https://skills.sh",
            "skills.sh",
            "skill_pattern",
            "Patrones de skills",
            project_key="otro-proyecto",
        )

        rows = self.database.list_external_references(project_key="july-unificada")

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["source_name"], "agents.md")

    def test_adopt_missing_contribution_preserves_error(self) -> None:
        with self.assertRaises(ValueError):
            self.database.adopt_contribution(999)


if __name__ == "__main__":
    unittest.main()
