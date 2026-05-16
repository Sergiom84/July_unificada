from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from july.cli import build_parser
from july.config import LLMSettings, Settings, UISettings
from july.db import JulyDatabase
from july.mcp import JulyMCPServer
from july.project_conversation import ProjectConversationService
from july.skill_registry import discover_local_skill_commands, load_skill_reference


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


class ProjectConversationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.db_path = self.root / "july-test.db"
        self.database = JulyDatabase(build_test_settings(self.db_path))
        self.service = ProjectConversationService(self.database)
        self.repo_root = self.root / "Dashboard_AV"
        (self.repo_root / "src").mkdir(parents=True)
        (self.repo_root / "README.md").write_text(
            "# Dashboard AV\n\nAplicacion para revisar metricas y automatizar paneles.\n",
            encoding="utf-8",
        )
        (self.repo_root / "package.json").write_text(
            json.dumps(
                {
                    "name": "dashboard-av",
                    "scripts": {"dev": "vite", "build": "vite build", "test": "vitest"},
                    "dependencies": {"exceljs": "^4.4.0"},
                }
            ),
            encoding="utf-8",
        )
        (self.repo_root / "src" / "index.ts").write_text(
            "import ExcelJS from 'exceljs';\nconsole.log('dashboard');\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_project_entry_returns_new_for_repo_without_context(self) -> None:
        result = self.service.project_entry(repo_path=str(self.repo_root))

        self.assertEqual(result["project_key"], "dashboard-av")
        self.assertEqual(result["project_state"], "new")
        self.assertEqual(result["profile"]["project_kind"], "web_app")
        self.assertIn("web_app", result["profile"]["project_tags"])
        self.assertTrue(result["profile"]["preferences"]["suggest_caveman"])
        self.assertEqual(result["recommended_action"], "analyze_now")
        self.assertEqual(result["options"][0]["action"], "analyze_now")
        self.assertTrue(any(option["action"] == "help" for option in result["options"]))
        self.assertIsNotNone(result["permission_request"])

    def test_project_onboard_saves_snapshot_and_keeps_repo_read_only(self) -> None:
        readme_before = (self.repo_root / "README.md").read_text(encoding="utf-8")

        result = self.service.project_onboard(repo_path=str(self.repo_root), agent_name="codex-test", source="test")
        project_ctx = self.database.project_context("dashboard-av")
        sessions = self.database.session_context(project_key="dashboard-av")

        self.assertTrue(result["stored"]["memory_item_id"])
        self.assertEqual(result["session"]["ended"]["status"], "closed")
        self.assertEqual(len(project_ctx["memory"]), 1)
        self.assertEqual(len(sessions), 1)
        self.assertEqual((self.repo_root / "README.md").read_text(encoding="utf-8"), readme_before)

    def test_project_entry_returns_known_after_onboarding(self) -> None:
        self.service.project_onboard(repo_path=str(self.repo_root), source="test")

        result = self.service.project_entry(repo_path=str(self.repo_root))

        self.assertEqual(result["project_state"], "known")
        self.assertEqual(result["recommended_action"], "resume_context")
        self.assertEqual(result["options"][0]["action"], "resume_context")

    def test_conversation_checkpoint_can_persist_clear_reusable_finding(self) -> None:
        result = self.service.conversation_checkpoint(
            "Decision: usar ExcelJS para exportaciones porque evita automatizaciones fragiles con COM.",
            repo_path=str(self.repo_root),
            persist=True,
            source="test",
        )

        self.assertEqual(result["action"], "store_directly")
        self.assertTrue(result["stored"]["memory_item_id"])

    def test_conversation_checkpoint_asks_for_tentative_note(self) -> None:
        result = self.service.conversation_checkpoint(
            "Quiz podria venir bien mover esto a otro modulo mas adelante.",
            repo_path=str(self.repo_root),
            source="test",
        )

        self.assertEqual(result["action"], "ask_user")
        self.assertIsNone(result["stored"])

    def test_project_action_analyze_now_delegates_to_onboarding(self) -> None:
        result = self.service.project_action("analyze_now", repo_path=str(self.repo_root), agent_name="codex-test")

        self.assertEqual(result["action"], "analyze_now")
        self.assertEqual(result["result"]["project_key"], "dashboard-av")
        self.assertTrue(result["result"]["stored"]["memory_item_id"])

    def test_project_action_continue_without_context_is_non_invasive(self) -> None:
        result = self.service.project_action("continue_without_context", repo_path=str(self.repo_root))

        self.assertEqual(result["action"], "continue_without_context")
        self.assertIn("sin releer ni guardar", result["message"])
        project_ctx = self.database.project_context("dashboard-av")
        self.assertEqual(project_ctx["memory"], [])

    def test_project_action_help_explains_knowns_unknowns_and_capabilities(self) -> None:
        result = self.service.project_action("help", repo_path=str(self.repo_root))

        self.assertEqual(result["action"], "help")
        self.assertIn("Ayuda de July", result["message"])
        self.assertTrue(any("Tipo detectado: web_app" in item for item in result["knows"]))
        self.assertTrue(result["unknowns"])
        self.assertTrue(any("onboarding" in item.lower() for item in result["can_do"]))

    def test_project_improvement_can_be_saved_and_listed(self) -> None:
        created = self.service.add_project_improvement(
            "Mejorar el panel de metricas con filtros por sede.",
            repo_path=str(self.repo_root),
            priority="high",
            source="test",
        )
        listed = self.service.list_project_improvements(repo_path=str(self.repo_root))
        project_ctx = self.database.project_context("dashboard-av")

        self.assertEqual(created["action"], "stored")
        self.assertEqual(created["improvement"]["priority"], "high")
        self.assertEqual(len(listed["improvements"]), 1)
        self.assertEqual(project_ctx["improvements"][0]["status"], "open")

    def test_project_improvement_status_can_be_closed(self) -> None:
        created = self.service.add_project_improvement(
            "Preparar modo compacto para la vista de usuarios.",
            repo_path=str(self.repo_root),
            source="test",
        )

        updated = self.service.update_project_improvement_status(
            created["improvement"]["id"],
            "done",
            repo_path=str(self.repo_root),
        )
        active = self.service.list_project_improvements(repo_path=str(self.repo_root))
        all_items = self.service.list_project_improvements(repo_path=str(self.repo_root), include_closed=True)

        self.assertEqual(updated["improvement"]["status"], "done")
        self.assertEqual(active["improvements"], [])
        self.assertEqual(all_items["improvements"][0]["status"], "done")

    def test_project_pending_can_be_saved_listed_and_closed(self) -> None:
        created = self.service.add_project_pending(
            "Pendiente: revisar el flujo de login en movil.",
            repo_path=str(self.repo_root),
            source="test",
        )
        listed = self.service.list_project_pendings(repo_path=str(self.repo_root))

        updated = self.service.update_project_pending_status(
            created["pending"]["id"],
            "done",
            repo_path=str(self.repo_root),
        )
        active = self.service.list_project_pendings(repo_path=str(self.repo_root))
        all_items = self.service.list_project_pendings(repo_path=str(self.repo_root), include_done=True)

        self.assertEqual(created["action"], "stored")
        self.assertEqual(listed["pendings"][0]["status"], "pending")
        self.assertEqual(updated["pending"]["status"], "done")
        self.assertEqual(active["pendings"], [])
        self.assertEqual(all_items["pendings"][0]["status"], "done")

    def test_skill_reference_can_be_registered_and_suggested(self) -> None:
        self.database.upsert_skill_reference(
            skill_name="entrevistador-procesos",
            display_name="entrevistador-procesos",
            description="Entrevista al usuario antes de crear procesos, workflows, automatizaciones o skills.",
            trigger_text=(
                "crear automatizar workflow proceso sistema proyecto skill definir requisitos "
                "reglas excepciones ejemplos antes de construir"
            ),
            domains=["skills", "procesos", "automatizacion"],
        )

        suggestions = self.database.suggest_skill_references(
            "Quiero crear una automatizacion pero no tengo claro el proceso ni las reglas.",
            project_key="dashboard-av",
        )
        recall = self.database.proactive_recall(
            "Necesito automatizar un workflow complejo antes de construirlo.",
            project_key="dashboard-av",
        )

        self.assertEqual(suggestions[0]["skill_name"], "entrevistador-procesos")
        self.assertEqual(recall["skill_suggestions"][0]["skill_name"], "entrevistador-procesos")

    def test_skill_reference_loader_reads_skill_archive(self) -> None:
        skill_path = self.root / "planificador-procesos.skill"
        with zipfile.ZipFile(skill_path, "w") as archive:
            archive.writestr(
                "entrevistador-procesos/SKILL.md",
                (
                    "---\n"
                    "name: entrevistador-procesos\n"
                    "description: Entrevista al usuario para definir procesos antes de construir.\n"
                    "---\n"
                    "# Entrevistador de Procesos\n\n"
                    "Usar cuando Sergio quiera crear, automatizar o documentar un proceso.\n"
                ),
            )

        draft = load_skill_reference(skill_path)

        self.assertEqual(draft.skill_name, "entrevistador-procesos")
        self.assertIn("definir procesos", draft.description)
        self.assertIn("automatizar", draft.trigger_text)

    def test_skill_reference_loader_reads_multiline_description(self) -> None:
        skill_path = self.root / "presentaciones-visuales.skill"
        with zipfile.ZipFile(skill_path, "w") as archive:
            archive.writestr(
                "presentaciones-visuales/SKILL.md",
                (
                    "---\n"
                    "name: presentaciones-visuales\n"
                    "description: >\n"
                    "  Crea presentaciones visuales modernas a partir de una idea.\n"
                    "  Úsala cuando el usuario quiera convertir contenido en slides.\n"
                    "---\n"
                    "# Presentaciones Visuales\n\n"
                    "Crea presentaciones HTML autocontenidas.\n"
                ),
            )

        draft = load_skill_reference(skill_path)

        self.assertEqual(draft.skill_name, "presentaciones-visuales")
        self.assertIn("presentaciones visuales modernas", draft.description)
        self.assertIn("convertir contenido en slides", draft.description)

    def test_local_skill_commands_are_discovered_separately(self) -> None:
        skills_root = self.root / "skills"
        command_dir = skills_root / "july"
        command_dir.mkdir(parents=True)
        (command_dir / "SKILL.md").write_text(
            (
                "---\n"
                "name: july\n"
                "description: Atajo principal para usar July como memoria local de proyecto.\n"
                "---\n"
                "# July\n"
            ),
            encoding="utf-8",
        )

        commands = discover_local_skill_commands(skills_root)

        self.assertEqual(commands[0]["type"], "local_skill_command")
        self.assertEqual(commands[0]["category"], "july_memory_command")
        self.assertEqual(commands[0]["skill_name"], "july")


class ExposureTests(unittest.TestCase):
    def test_cli_parser_includes_project_commands(self) -> None:
        parser = build_parser()
        choices = parser._subparsers._group_actions[0].choices  # type: ignore[attr-defined]

        self.assertIn("project-entry", choices)
        self.assertIn("project-onboard", choices)
        self.assertIn("project-action", choices)
        self.assertIn("conversation-checkpoint", choices)
        self.assertIn("improvement-add", choices)
        self.assertIn("improvements", choices)
        self.assertIn("improvement-status", choices)
        self.assertIn("pending-add", choices)
        self.assertIn("pendings", choices)
        self.assertIn("pending-status", choices)
        self.assertIn("ui", choices)
        self.assertIn("ui-link", choices)
        self.assertIn("skill-register", choices)
        self.assertIn("skills", choices)
        self.assertIn("skill-suggest", choices)

        project_action = choices["project-action"]
        action = project_action._actions[1]  # type: ignore[attr-defined]
        self.assertIn("help", action.choices)

    def test_mcp_server_exposes_project_tools(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = build_test_settings(Path(temp_dir) / "july-test.db")
            with patch("july.mcp.get_settings", return_value=settings):
                server = JulyMCPServer()

        self.assertIn("project_entry", server.tools)
        self.assertIn("project_onboard", server.tools)
        self.assertIn("project_action", server.tools)
        self.assertIn("conversation_checkpoint", server.tools)
        self.assertIn("project_ui_link", server.tools)
        self.assertIn("project_improvement_add", server.tools)
        self.assertIn("project_improvements", server.tools)
        self.assertIn("project_improvement_status", server.tools)
        self.assertIn("project_pending_add", server.tools)
        self.assertIn("project_pendings", server.tools)
        self.assertIn("project_pending_status", server.tools)
        self.assertIn("skill_register", server.tools)
        self.assertIn("skill_references", server.tools)
        self.assertIn("skill_suggest", server.tools)

    def test_mcp_skill_references_separates_local_commands(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = build_test_settings(Path(temp_dir) / "july-test.db")
            with patch("july.mcp.get_settings", return_value=settings), patch(
                "july.mcp_tools.references_skills.discover_local_skill_commands",
                return_value=[{"type": "local_skill_command", "skill_name": "july"}],
            ):
                server = JulyMCPServer()
                result = server.tool_skill_references({})

        self.assertIn("skills", result)
        self.assertEqual(result["local_commands"][0]["skill_name"], "july")


if __name__ == "__main__":
    unittest.main()
