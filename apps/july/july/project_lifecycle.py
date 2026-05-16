from __future__ import annotations

from collections.abc import Callable
from typing import Any

from july.db import JulyDatabase
from july.pipeline import apply_classification_overrides, create_capture_plan
from july.project_memory_actions import ProjectMemoryActions
from july.project_messages import (
    build_distilled_knowledge,
    build_project_help,
    build_session_key,
    build_snapshot_summary,
    build_snapshot_text,
    compare_repository_with_context,
    extract_next_step,
    suggest_next_step,
)
from july.project_surface import (
    analyze_repository,
    infer_project_profile,
    inspect_repository_surface,
    resolve_project_identity,
)


class ProjectLifecycleActions:
    def __init__(self, database: JulyDatabase, memory_actions: ProjectMemoryActions) -> None:
        self.database = database
        self.memory_actions = memory_actions

    def project_onboard(
        self,
        *,
        repo_path: str | None = None,
        project_key: str | None = None,
        agent_name: str | None = None,
        source: str = "wizard",
    ) -> dict[str, Any]:
        repo_root, resolved_project_key = resolve_project_identity(self.database, repo_path=repo_path, project_key=project_key)
        surface = inspect_repository_surface(repo_root)
        profile = infer_project_profile(repo_root, surface)
        self.database.upsert_project(
            resolved_project_key,
            str(repo_root),
            repo_name=repo_root.name,
            project_kind=profile.project_kind,
            project_tags=profile.project_tags,
            preferences=profile.preferences,
        )
        analysis = analyze_repository(repo_root)
        session_key = build_session_key(resolved_project_key, prefix="onboard")

        session = self.database.session_start(
            session_key,
            project_key=resolved_project_key,
            agent_name=agent_name or "july",
            goal=f"Onboarding inicial de {resolved_project_key}",
        )

        snapshot_text = build_snapshot_text(resolved_project_key, analysis)
        plan = create_capture_plan(snapshot_text)
        plan = apply_classification_overrides(
            snapshot_text,
            plan,
            {
                "intent": "repository_onboarding",
                "confidence": 0.95,
                "status": "ready",
                "normalized_summary": f"Onboarding inicial de proyecto: {resolved_project_key}",
                "clarification_question": None,
                "domain": "Programacion",
                "project_key": resolved_project_key,
            },
        )
        plan["task"] = None
        plan["memory"] = {
            "memory_kind": "semantic",
            "title": f"Perfil inicial del proyecto {resolved_project_key}",
            "summary": build_snapshot_summary(analysis),
            "distilled_knowledge": build_distilled_knowledge(analysis),
            "domain": "Programacion",
            "scope": "project",
            "project_key": resolved_project_key,
            "importance": 4,
            "confidence": 0.95,
            "status": "ready",
        }
        capture_result = self.database.capture(snapshot_text, source, str(repo_root), plan)
        topic_link = self.memory_actions.maybe_link_topic(snapshot_text, capture_result["memory_item_id"])

        summary = f"Onboarding inicial completado para {resolved_project_key}."
        discoveries = build_snapshot_summary(analysis)
        next_steps = "; ".join(analysis["open_questions"]) if analysis["open_questions"] else suggest_next_step(analysis)
        relevant_files = ", ".join(analysis["files_read"])
        self.database.session_summary(
            session_key,
            summary=summary,
            discoveries=discoveries,
            next_steps=next_steps,
            relevant_files=relevant_files,
        )
        ended = self.database.session_end(session_key)

        return {
            "project_key": resolved_project_key,
            "repo_root": str(repo_root),
            "analysis": analysis,
            "snapshot": {
                "text": snapshot_text,
                "summary": build_snapshot_summary(analysis),
                "next_steps": next_steps,
            },
            "stored": capture_result,
            "session": {"started": session, "ended": ended, "session_key": session_key},
            "topic_link": topic_link,
        }

    def project_action(
        self,
        action: str,
        *,
        repo_path: str | None = None,
        project_key: str | None = None,
        agent_name: str | None = None,
        entry_builder: Callable[..., dict[str, Any]],
    ) -> dict[str, Any]:
        repo_root, resolved_project_key = resolve_project_identity(self.database, repo_path=repo_path, project_key=project_key)
        surface = inspect_repository_surface(repo_root)
        profile = infer_project_profile(repo_root, surface)
        self.database.upsert_project(
            resolved_project_key,
            str(repo_root),
            repo_name=repo_root.name,
            project_kind=profile.project_kind,
            project_tags=profile.project_tags,
            preferences=profile.preferences,
        )
        entry = entry_builder(repo_path=str(repo_root), project_key=resolved_project_key)

        if action == "analyze_now":
            return {
                "action": action,
                "project_key": resolved_project_key,
                "result": self.project_onboard(
                    repo_path=str(repo_root),
                    project_key=resolved_project_key,
                    agent_name=agent_name,
                ),
            }

        if action == "resume_context":
            return {
                "action": action,
                "project_key": resolved_project_key,
                "message": (
                    f"Este proyecto ya tiene contexto util en July. "
                    f"{entry['context_summary']}"
                ),
                "next_step": extract_next_step(entry["related_context"], entry["context_summary"]),
            }

        if action == "refresh_context":
            analysis = analyze_repository(repo_root)
            comparison = compare_repository_with_context(analysis, entry["context_summary"])
            return {
                "action": action,
                "project_key": resolved_project_key,
                "message": (
                    "He hecho una revision selectiva y superficial del repo para refrescar el contexto."
                ),
                "refresh_summary": comparison,
                "analysis": analysis,
            }

        if action == "continue_without_context":
            return {
                "action": action,
                "project_key": resolved_project_key,
                "message": (
                    "Sigo contigo sin releer ni guardar nada ahora mismo. "
                    "Si encuentro una decision reutilizable, te preguntare si quieres guardarla."
                ),
            }

        if action == "help":
            return {
                "action": action,
                "project_key": resolved_project_key,
                **build_project_help(entry),
            }

        if action == "wait":
            return {
                "action": action,
                "project_key": resolved_project_key,
                "message": "Perfecto. Espero y no analizo el repo todavia.",
            }

        if action == "do_nothing":
            return {
                "action": action,
                "project_key": resolved_project_key,
                "message": "No hago nada por ahora.",
            }

        raise ValueError(f"Unsupported project action: {action}")

