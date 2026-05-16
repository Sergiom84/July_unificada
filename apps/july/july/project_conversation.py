from __future__ import annotations

import json
from typing import Any

from july.analyzer import analyze_codebase
from july.db import JulyDatabase
from july.project_lifecycle import ProjectLifecycleActions
from july.project_messages import (
    assess_project_state,
    build_context_summary,
    build_copilot_hint,
    build_entry_message,
    build_entry_options,
    build_permission_request,
    build_project_help,
    build_recall_query,
    build_session_key,
    recommended_action_for_state,
)
from july.project_memory_actions import ProjectMemoryActions
from july.project_surface import (
    derive_project_key,
    detect_repo_root,
    infer_project_profile,
    inspect_repository_surface,
    resolve_project_identity,
)


class ProjectConversationService:
    def __init__(self, database: JulyDatabase) -> None:
        self.database = database
        self.memory_actions = ProjectMemoryActions(database)
        self.lifecycle_actions = ProjectLifecycleActions(database, self.memory_actions)

    def project_entry(
        self,
        *,
        repo_path: str | None = None,
        project_key: str | None = None,
        limit: int = 5,
    ) -> dict[str, Any]:
        repo_root, resolved_project_key = resolve_project_identity(self.database, repo_path=repo_path, project_key=project_key)
        surface = inspect_repository_surface(repo_root)
        profile = infer_project_profile(repo_root, surface)
        project = self.database.upsert_project(
            resolved_project_key,
            str(repo_root),
            repo_name=repo_root.name,
            project_kind=profile.project_kind,
            project_tags=profile.project_tags,
            preferences=profile.preferences,
        )
        project_ctx = self.database.project_context(resolved_project_key, limit=limit)
        sessions = self.database.session_context(project_key=resolved_project_key, limit=limit)
        project_state = assess_project_state(project_ctx, sessions)
        context_summary = build_context_summary(resolved_project_key, project_ctx, sessions, surface)
        recall = self.database.proactive_recall(
            build_recall_query(resolved_project_key, context_summary, surface),
            project_key=resolved_project_key,
            limit=3,
        )

        # Developer level for adaptive responses
        developer_level = self.database.get_developer_level()

        # Deep code analysis for proactive architect insights
        code_analysis = analyze_codebase(repo_root)
        architect = {
            "architecture_pattern": code_analysis.architecture_pattern,
            "insights": [
                {"pattern": i.pattern, "confidence": i.confidence,
                 "detail": i.detail, "suggestion": i.suggestion}
                for i in code_analysis.architecture_insights
            ],
            "code_smells_count": len(code_analysis.code_smells),
            "top_smells": [
                {"file": s.file, "kind": s.kind, "detail": s.detail, "severity": s.severity}
                for s in code_analysis.code_smells[:5]
            ],
            "proactive_questions": code_analysis.proactive_questions,
            "suggestions": code_analysis.suggestions,
            "languages": code_analysis.languages,
            "source_files": code_analysis.source_files,
        }

        return {
            "project_key": resolved_project_key,
            "repo_root": str(repo_root),
            "project_state": project_state,
            "context_summary": context_summary,
            "entry_message": build_entry_message(project_state, surface, context_summary),
            "permission_request": build_permission_request(project_state, surface),
            "recommended_action": recommended_action_for_state(project_state),
            "options": build_entry_options(project_state),
            "surface": {
                "repo_name": surface.repo_name,
                "docs": surface.docs,
                "manifests": surface.manifests,
                "entrypoints": surface.entrypoints,
                "stack": surface.stack,
            },
            "profile": {
                "project_kind": project["project_kind"],
                "project_tags": json.loads(project["project_tags_json"]),
                "preferences": json.loads(project["preferences_json"]),
            },
            "related_context": recall,
            "architect": architect,
            "developer_level": developer_level,
            "copilot_hint": build_copilot_hint(developer_level, architect),
        }

    def project_onboard(
        self,
        *,
        repo_path: str | None = None,
        project_key: str | None = None,
        agent_name: str | None = None,
        source: str = "wizard",
    ) -> dict[str, Any]:
        return self.lifecycle_actions.project_onboard(
            repo_path=repo_path,
            project_key=project_key,
            agent_name=agent_name,
            source=source,
        )

    def project_action(
        self,
        action: str,
        *,
        repo_path: str | None = None,
        project_key: str | None = None,
        agent_name: str | None = None,
    ) -> dict[str, Any]:
        return self.lifecycle_actions.project_action(
            action,
            repo_path=repo_path,
            project_key=project_key,
            agent_name=agent_name,
            entry_builder=self.project_entry,
        )

    def conversation_checkpoint(
        self,
        text: str,
        *,
        repo_path: str | None = None,
        project_key: str | None = None,
        persist: bool = False,
        source: str = "wizard",
    ) -> dict[str, Any]:
        return self.memory_actions.conversation_checkpoint(
            text,
            repo_path=repo_path,
            project_key=project_key,
            persist=persist,
            source=source,
        )

    def save_decision(
        self,
        text: str,
        *,
        repo_path: str | None = None,
        project_key: str | None = None,
        source: str = "ui",
    ) -> dict[str, Any]:
        return self.memory_actions.save_decision(
            text,
            repo_path=repo_path,
            project_key=project_key,
            source=source,
        )

    def save_finding(
        self,
        text: str,
        *,
        repo_path: str | None = None,
        project_key: str | None = None,
        source: str = "ui",
    ) -> dict[str, Any]:
        return self.memory_actions.save_finding(
            text,
            repo_path=repo_path,
            project_key=project_key,
            source=source,
        )

    def add_project_improvement(
        self,
        text: str,
        *,
        repo_path: str | None = None,
        project_key: str | None = None,
        priority: str = "normal",
        source: str = "wizard",
    ) -> dict[str, Any]:
        return self.memory_actions.add_project_improvement(
            text,
            repo_path=repo_path,
            project_key=project_key,
            priority=priority,
            source=source,
        )

    def list_project_improvements(
        self,
        *,
        repo_path: str | None = None,
        project_key: str | None = None,
        status: str | None = None,
        include_closed: bool = False,
        limit: int = 20,
    ) -> dict[str, Any]:
        return self.memory_actions.list_project_improvements(
            repo_path=repo_path,
            project_key=project_key,
            status=status,
            include_closed=include_closed,
            limit=limit,
        )

    def update_project_improvement_status(
        self,
        improvement_id: int,
        status: str,
        *,
        repo_path: str | None = None,
        project_key: str | None = None,
    ) -> dict[str, Any]:
        return self.memory_actions.update_project_improvement_status(
            improvement_id,
            status,
            repo_path=repo_path,
            project_key=project_key,
        )

    def add_project_pending(
        self,
        text: str,
        *,
        repo_path: str | None = None,
        project_key: str | None = None,
        source: str = "wizard",
    ) -> dict[str, Any]:
        return self.memory_actions.add_project_pending(
            text,
            repo_path=repo_path,
            project_key=project_key,
            source=source,
        )

    def list_project_pendings(
        self,
        *,
        repo_path: str | None = None,
        project_key: str | None = None,
        status: str | None = None,
        include_done: bool = False,
        limit: int = 20,
    ) -> dict[str, Any]:
        return self.memory_actions.list_project_pendings(
            repo_path=repo_path,
            project_key=project_key,
            status=status,
            include_done=include_done,
            limit=limit,
        )

    def update_project_pending_status(
        self,
        pending_id: int,
        status: str,
        *,
        repo_path: str | None = None,
        project_key: str | None = None,
    ) -> dict[str, Any]:
        return self.memory_actions.update_project_pending_status(
            pending_id,
            status,
            repo_path=repo_path,
            project_key=project_key,
        )

    def _store_checkpoint(self, text: str, project_key: str, kind: str, source: str) -> dict[str, Any]:
        return self.memory_actions.store_checkpoint(text, project_key, kind, source)

    def _maybe_link_topic(self, text: str, memory_item_id: int | None) -> dict[str, Any] | None:
        return self.memory_actions.maybe_link_topic(text, memory_item_id)
