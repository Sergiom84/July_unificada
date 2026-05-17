from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from july.config import LLMSettings, Settings, UISettings
from july.db import JulyDatabase
from july.mcp import JulyMCPServer
from july.project_conversation import ProjectConversationService
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


class MemoryAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.database = JulyDatabase(build_test_settings(self.root / "july-test.db"))
        self.repo_root = self.root / "Indalo_padel"
        (self.repo_root / "backend").mkdir(parents=True)
        (self.repo_root / "backend" / "server.js").write_text("console.log('server')", encoding="utf-8")
        (self.repo_root / "README.md").write_text("# Indalo Padel\n", encoding="utf-8")
        self.service = ProjectConversationService(self.database)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_memory_audit_detects_low_quality_obsolete_and_duplicate_memory(self) -> None:
        self._insert_memory(
            "Perfil inicial del proyecto indalo-padel",
            "Stack: No detectado. Entrypoints: ninguno detectado.",
            "No hay una descripción explicita y las mÃ©tricas se ven mal.",
        )
        self._insert_memory(
            "Perfil inicial del proyecto indalo-padel actualizado",
            "Entrypoints detectados.",
            "backend/server.js detectado.",
        )

        preview = self.service.audit_memory(
            repo_path=str(self.repo_root),
            dry_run=True,
            limit=10,
        )
        self.assertTrue(preview["dry_run"])
        self.assertEqual(self.database.memory_audit_summary("indalo-padel")["open_count"], 0)

        result = self.service.audit_memory(
            repo_path=str(self.repo_root),
            dry_run=False,
            limit=10,
        )
        finding_types = {finding["finding_type"] for finding in result["findings"]}

        self.assertIn("low_quality", finding_types)
        self.assertIn("possibly_obsolete", finding_types)
        self.assertIn("duplicate", finding_types)
        self.assertGreaterEqual(self.database.memory_audit_summary("indalo-padel")["open_count"], 3)

    def test_memory_audit_resolve_can_archive_memory_after_confirmation(self) -> None:
        memory_id = self._insert_memory(
            "Perfil inicial del proyecto indalo-padel",
            "Entrypoints: ninguno detectado.",
            "Stack: No detectado.",
        )
        result = self.database.audit_memory(
            "indalo-padel",
            current_entrypoints=["backend/server.js"],
            dry_run=False,
            limit=5,
        )
        finding = next(item for item in result["findings"] if item["subject_id"] == memory_id)

        resolved = self.database.resolve_memory_audit_finding(
            finding["id"],
            "resolved",
            review_notes="Confirmado por test.",
            reviewed_by="unittest",
            apply_memory_status="archived",
        )
        memory = self.database.get_record("memory_items", memory_id)

        self.assertEqual(resolved["finding"]["status"], "resolved")
        self.assertEqual(resolved["applied"]["status"], "archived")
        self.assertEqual(memory["status"], "archived")

    def test_memory_audit_detects_pending_possibly_completed_by_later_memory(self) -> None:
        timestamp = utc_now()
        with self.database.connection() as conn:
            task = conn.execute(
                """
                INSERT INTO tasks (
                    inbox_item_id, task_type, status, title, details, project_key,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    None,
                    "manual_follow_up",
                    "pending",
                    "Pendiente: hacer QA móvil convocatorias",
                    "Revisar QA móvil de convocatorias demo.",
                    "indalo-padel",
                    timestamp,
                    timestamp,
                ),
            )
        self._insert_memory(
            "QA convocatorias demo actualizado 2026-05-17",
            "QA móvil de convocatorias demo validado.",
            "Planes validados y flujo probado.",
        )

        result = self.database.audit_memory("indalo-padel", dry_run=False)
        completed = [item for item in result["findings"] if item["finding_type"] == "possibly_completed"]

        self.assertTrue(completed)
        self.assertEqual(completed[0]["subject_table"], "tasks")
        self.assertEqual(completed[0]["subject_id"], task.lastrowid)

    def test_project_entry_includes_memory_hygiene_summary(self) -> None:
        self._insert_memory(
            "Perfil inicial del proyecto indalo-padel",
            "Stack: No detectado.",
            "Entrypoints: ninguno detectado.",
        )
        self.service.audit_memory(repo_path=str(self.repo_root), dry_run=False)

        entry = self.service.project_entry(repo_path=str(self.repo_root))

        self.assertIn("memory_hygiene", entry)
        self.assertTrue(entry["memory_hygiene"]["needs_review"])

    def test_mcp_server_exposes_memory_audit_tools(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = build_test_settings(Path(temp_dir) / "july-test.db")
            with patch("july.mcp.get_settings", return_value=settings):
                server = JulyMCPServer()

        self.assertIn("memory_audit", server.tools)
        self.assertIn("memory_audit_findings", server.tools)
        self.assertIn("memory_audit_resolve", server.tools)

    def _insert_memory(self, title: str, summary: str, knowledge: str) -> int:
        timestamp = utc_now()
        with self.database.connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO memory_items (
                    inbox_item_id, memory_kind, title, summary, distilled_knowledge, domain,
                    scope, project_key, importance, confidence, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    None,
                    "semantic",
                    title,
                    summary,
                    knowledge,
                    "tests",
                    "project",
                    "indalo-padel",
                    3,
                    0.9,
                    "ready",
                    timestamp,
                    timestamp,
                ),
            )
        return int(cursor.lastrowid)
