from __future__ import annotations

from typing import Any
from urllib.parse import quote

from july.config import Settings
from july.cockpit_builders import (
    build_activity_feed,
    build_best_practice_suggestions,
    rows_to_dicts,
)
from july.db import JulyDatabase
from july.project_conversation import (
    ProjectConversationService,
    build_session_key,
    resolve_project_identity,
)


def build_ui_base_url(settings: Settings) -> str:
    if settings.ui.base_url:
        return settings.ui.base_url.rstrip("/")

    host = settings.ui.host
    if host in {"0.0.0.0", "::"}:
        host = "127.0.0.1"
    return f"http://{host}:{settings.ui.port}"


def build_project_ui_url(settings: Settings, project_key: str) -> str:
    return f"{build_ui_base_url(settings)}/projects/{quote(project_key)}"


class ProjectCockpitService:
    def __init__(
        self,
        database: JulyDatabase,
        settings: Settings,
        project_service: ProjectConversationService | None = None,
    ) -> None:
        self.database = database
        self.settings = settings
        self.project_service = project_service or ProjectConversationService(database)

    def list_recent_projects(self, limit: int = 20) -> list[dict[str, Any]]:
        return self.database.list_projects(limit=limit)

    def open_project(
        self,
        *,
        repo_path: str | None = None,
        project_key: str | None = None,
    ) -> dict[str, Any]:
        if not repo_path and project_key:
            existing = self.database.touch_project(project_key)
            if existing is not None:
                return {
                    **existing,
                    "url": build_project_ui_url(self.settings, existing["project_key"]),
                }
            raise ValueError(
                f"Project {project_key} not found in the registry. Provide repo_path to register it first."
            )

        repo_root, resolved_project_key = resolve_project_identity(
            self.database,
            repo_path=repo_path,
            project_key=project_key,
        )
        project = self.database.upsert_project(
            resolved_project_key,
            str(repo_root),
            repo_name=repo_root.name,
        )
        return {
            **project,
            "url": build_project_ui_url(self.settings, resolved_project_key),
        }

    def project_ui_link(
        self,
        *,
        project_key: str,
        repo_path: str | None = None,
    ) -> dict[str, Any]:
        project = self.open_project(repo_path=repo_path, project_key=project_key)
        return {
            "url": project["url"],
            "project_key": project["project_key"],
            "repo_root": project["repo_root"],
        }

    def build_cockpit(
        self,
        *,
        project_key: str,
        repo_path: str | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        project = self.open_project(repo_path=repo_path, project_key=project_key)
        entry = self.project_service.project_entry(
            repo_path=project["repo_root"],
            project_key=project["project_key"],
            limit=limit,
        )
        project_context = rows_to_dicts(
            self.database.project_context(project["project_key"], limit=limit)
        )
        totals = self.database.get_project_totals(project["project_key"])
        sessions = self.database.session_context(project_key=project["project_key"], limit=limit)
        active_session = self.database.get_open_session(project["project_key"])
        distillation = self.database.distill_candidates(project["project_key"], limit=5)
        recent_memory = project_context["memory"]
        recent_inbox = project_context["inbox"]
        recent_findings = [
            item for item in recent_memory
            if item["title"].lower().startswith("hallazgo")
        ]
        pending_tasks = [
            item for item in project_context["tasks"]
            if item["status"] != "done"
        ]
        pending_improvements = [
            item for item in project_context["improvements"]
            if item["status"] in {"open", "planned", "in_progress"}
        ]
        suggestions = build_best_practice_suggestions(
            entry=entry,
            active_session=active_session,
            pending_tasks=pending_tasks,
            pending_improvements=pending_improvements,
            recent_memory=recent_memory,
            sessions=sessions,
            distillation=distillation,
        )

        return {
            "project": project,
            "ui_url": project["url"],
            "entry": entry,
            "stats": totals,
            "project_context": project_context,
            "active_session": active_session,
            "last_session": sessions[0] if sessions else None,
            "recent_sessions": sessions[:5],
            "recent_inbox": recent_inbox,
            "recent_findings": recent_findings,
            "pending_tasks": pending_tasks,
            "pending_improvements": pending_improvements,
            "distillation": distillation,
            "suggestions": suggestions,
            "activity_feed": build_activity_feed(
                memory_items=recent_memory,
                inbox_items=recent_inbox,
                sessions=sessions,
                tasks=pending_tasks,
                improvements=pending_improvements,
                findings=recent_findings,
            ),
        }

    def review_project(
        self,
        *,
        project_key: str,
        mode: str,
        repo_path: str | None = None,
        agent_name: str = "july-ui",
    ) -> dict[str, Any]:
        if mode not in {"analyze_now", "refresh_context", "resume_context", "help"}:
            raise ValueError("Review mode must be analyze_now, refresh_context, resume_context, or help")

        project = self.open_project(repo_path=repo_path, project_key=project_key)
        return self.project_service.project_action(
            mode,
            repo_path=project["repo_root"],
            project_key=project["project_key"],
            agent_name=agent_name,
        )

    def save_decision(
        self,
        *,
        project_key: str,
        text: str,
        repo_path: str | None = None,
    ) -> dict[str, Any]:
        project = self.open_project(repo_path=repo_path, project_key=project_key)
        return self.project_service.save_decision(
            text,
            repo_path=project["repo_root"],
            project_key=project["project_key"],
            source="ui",
        )

    def save_finding(
        self,
        *,
        project_key: str,
        text: str,
        repo_path: str | None = None,
    ) -> dict[str, Any]:
        project = self.open_project(repo_path=repo_path, project_key=project_key)
        return self.project_service.save_finding(
            text,
            repo_path=project["repo_root"],
            project_key=project["project_key"],
            source="ui",
        )

    def create_task(
        self,
        *,
        project_key: str,
        title: str,
        details: str | None = None,
        status: str = "pending",
    ) -> dict[str, Any]:
        self.open_project(project_key=project_key)
        return self.database.create_manual_task(
            project_key,
            title,
            details=details,
            status=status,
        )

    def create_improvement(
        self,
        *,
        project_key: str,
        text: str,
        priority: str = "normal",
    ) -> dict[str, Any]:
        project = self.open_project(project_key=project_key)
        return self.project_service.add_project_improvement(
            text,
            repo_path=project["repo_root"],
            project_key=project["project_key"],
            priority=priority,
            source="ui",
        )

    def update_improvement_status(
        self,
        *,
        project_key: str,
        improvement_id: int,
        status: str,
    ) -> dict[str, Any]:
        project = self.open_project(project_key=project_key)
        return self.project_service.update_project_improvement_status(
            improvement_id,
            status,
            repo_path=project["repo_root"],
            project_key=project["project_key"],
        )

    def update_task_status(
        self,
        *,
        project_key: str,
        task_id: int,
        status: str,
    ) -> dict[str, Any]:
        self.open_project(project_key=project_key)
        return self.database.update_task_status(task_id, status, project_key=project_key)

    def start_session(
        self,
        *,
        project_key: str,
        goal: str | None = None,
        agent_name: str = "july-ui",
    ) -> dict[str, Any]:
        self.open_project(project_key=project_key)
        existing = self.database.get_open_session(project_key)
        if existing is not None:
            return {"reused": True, "session": existing}

        session_key = build_session_key(project_key, prefix="ui")
        session = self.database.session_start(
            session_key,
            project_key=project_key,
            agent_name=agent_name,
            goal=goal or f"Sesion activa desde cockpit de {project_key}",
        )
        return {"reused": False, "session": session}

    def prepare_next_session(
        self,
        *,
        project_key: str,
        summary: str,
        discoveries: str | None = None,
        accomplished: str | None = None,
        next_steps: str | None = None,
        relevant_files: str | None = None,
        close_after_summary: bool = False,
    ) -> dict[str, Any]:
        open_session = self.database.get_open_session(project_key)
        if open_session is None:
            raise ValueError(f"No active session found for project {project_key}")

        summary_result = self.database.session_summary(
            open_session["session_key"],
            summary=summary,
            discoveries=discoveries,
            accomplished=accomplished,
            next_steps=next_steps,
            relevant_files=relevant_files,
        )
        ended = None
        if close_after_summary:
            ended = self.database.session_end(open_session["session_key"])
        return {"summary": summary_result, "ended": ended}

    def end_session(self, *, project_key: str) -> dict[str, Any]:
        open_session = self.database.get_open_session(project_key)
        if open_session is None:
            raise ValueError(f"No active session found for project {project_key}")
        return self.database.session_end(open_session["session_key"])
