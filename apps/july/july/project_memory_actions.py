from __future__ import annotations

from typing import Any

from july.db import JulyDatabase
from july.pipeline import apply_classification_overrides, create_capture_plan
from july.project_checkpoints import (
    SENSITIVE_PATTERNS,
    TOPIC_PATTERNS,
    build_checkpoint_title,
    build_improvement_title,
    build_pending_title,
    classify_checkpoint,
)
from july.project_surface import resolve_project_identity
from july.project_text import summarize_text


class ProjectMemoryActions:
    def __init__(self, database: JulyDatabase) -> None:
        self.database = database

    def conversation_checkpoint(
        self,
        text: str,
        *,
        repo_path: str | None = None,
        project_key: str | None = None,
        persist: bool = False,
        source: str = "wizard",
    ) -> dict[str, Any]:
        repo_root, resolved_project_key = resolve_project_identity(self.database, repo_path=repo_path, project_key=project_key)
        self.database.upsert_project(
            resolved_project_key,
            str(repo_root),
            repo_name=repo_root.name,
        )
        action, reason, kind = classify_checkpoint(text)

        stored = None
        confirmation_applied = False
        effective_action = action
        if action == "ask_user" and persist:
            effective_action = "store_directly"
            confirmation_applied = True

        if effective_action == "store_directly":
            stored = self.store_checkpoint(text, resolved_project_key, kind, source)

        return {
            "project_key": resolved_project_key,
            "action": effective_action,
            "reason": reason if not confirmation_applied else f"{reason} Confirmacion aplicada por el agente.",
            "kind": kind,
            "stored": stored,
            "confirmation_applied": confirmation_applied,
        }

    def save_decision(
        self,
        text: str,
        *,
        repo_path: str | None = None,
        project_key: str | None = None,
        source: str = "ui",
    ) -> dict[str, Any]:
        repo_root, resolved_project_key = resolve_project_identity(self.database, repo_path=repo_path, project_key=project_key)
        self.database.upsert_project(
            resolved_project_key,
            str(repo_root),
            repo_name=repo_root.name,
        )
        stored = self.store_checkpoint(text, resolved_project_key, "decision", source)
        return {
            "project_key": resolved_project_key,
            "action": "store_directly",
            "reason": "Decision estructurada guardada desde una accion explicita.",
            "kind": "decision",
            "stored": stored,
        }

    def save_finding(
        self,
        text: str,
        *,
        repo_path: str | None = None,
        project_key: str | None = None,
        source: str = "ui",
    ) -> dict[str, Any]:
        repo_root, resolved_project_key = resolve_project_identity(self.database, repo_path=repo_path, project_key=project_key)
        self.database.upsert_project(
            resolved_project_key,
            str(repo_root),
            repo_name=repo_root.name,
        )
        stored = self.store_checkpoint(text, resolved_project_key, "finding", source)
        return {
            "project_key": resolved_project_key,
            "action": "store_directly",
            "reason": "Hallazgo estructurado guardado desde una accion explicita.",
            "kind": "finding",
            "stored": stored,
        }

    def add_project_improvement(
        self,
        text: str,
        *,
        repo_path: str | None = None,
        project_key: str | None = None,
        priority: str = "normal",
        source: str = "wizard",
    ) -> dict[str, Any]:
        if any(pattern in text.lower() for pattern in SENSITIVE_PATTERNS):
            return {
                "project_key": project_key,
                "action": "ignored",
                "reason": "La idea parece contener informacion sensible. No la guardo en July.",
                "improvement": None,
            }

        repo_root, resolved_project_key = resolve_project_identity(self.database, repo_path=repo_path, project_key=project_key)
        self.database.upsert_project(
            resolved_project_key,
            str(repo_root),
            repo_name=repo_root.name,
        )
        improvement = self.database.create_project_improvement(
            resolved_project_key,
            build_improvement_title(text),
            description=text,
            priority=priority,
            source_channel=source,
            source_ref=str(repo_root),
        )
        return {
            "project_key": resolved_project_key,
            "action": "stored",
            "reason": "Mejora posible guardada para revisar o implementar mas adelante.",
            "improvement": improvement,
        }

    def list_project_improvements(
        self,
        *,
        repo_path: str | None = None,
        project_key: str | None = None,
        status: str | None = None,
        include_closed: bool = False,
        limit: int = 20,
    ) -> dict[str, Any]:
        repo_root, resolved_project_key = resolve_project_identity(self.database, repo_path=repo_path, project_key=project_key)
        self.database.upsert_project(
            resolved_project_key,
            str(repo_root),
            repo_name=repo_root.name,
        )
        improvements = self.database.list_project_improvements(
            resolved_project_key,
            status=status,
            include_closed=include_closed,
            limit=limit,
        )
        return {
            "project_key": resolved_project_key,
            "improvements": [dict(row) for row in improvements],
        }

    def update_project_improvement_status(
        self,
        improvement_id: int,
        status: str,
        *,
        repo_path: str | None = None,
        project_key: str | None = None,
    ) -> dict[str, Any]:
        repo_root, resolved_project_key = resolve_project_identity(self.database, repo_path=repo_path, project_key=project_key)
        self.database.upsert_project(
            resolved_project_key,
            str(repo_root),
            repo_name=repo_root.name,
        )
        improvement = self.database.update_project_improvement_status(
            improvement_id,
            status,
            project_key=resolved_project_key,
        )
        return {
            "project_key": resolved_project_key,
            "improvement": improvement,
        }

    def add_project_pending(
        self,
        text: str,
        *,
        repo_path: str | None = None,
        project_key: str | None = None,
        source: str = "wizard",
    ) -> dict[str, Any]:
        if any(pattern in text.lower() for pattern in SENSITIVE_PATTERNS):
            return {
                "project_key": project_key,
                "action": "ignored",
                "reason": "El pendiente parece contener informacion sensible. No lo guardo en July.",
                "pending": None,
            }

        repo_root, resolved_project_key = resolve_project_identity(self.database, repo_path=repo_path, project_key=project_key)
        self.database.upsert_project(
            resolved_project_key,
            str(repo_root),
            repo_name=repo_root.name,
        )
        pending = self.database.create_manual_task(
            resolved_project_key,
            build_pending_title(text),
            details=text,
            status="pending",
        )
        return {
            "project_key": resolved_project_key,
            "action": "stored",
            "reason": "Pendiente guardado. Debe marcarse como done cuando se complete.",
            "source": source,
            "pending": pending,
        }

    def list_project_pendings(
        self,
        *,
        repo_path: str | None = None,
        project_key: str | None = None,
        status: str | None = None,
        include_done: bool = False,
        limit: int = 20,
    ) -> dict[str, Any]:
        repo_root, resolved_project_key = resolve_project_identity(self.database, repo_path=repo_path, project_key=project_key)
        self.database.upsert_project(
            resolved_project_key,
            str(repo_root),
            repo_name=repo_root.name,
        )
        pendings = self.database.list_project_tasks(
            resolved_project_key,
            status=status,
            include_done=include_done,
            limit=limit,
        )
        return {
            "project_key": resolved_project_key,
            "pendings": [dict(row) for row in pendings],
        }

    def update_project_pending_status(
        self,
        pending_id: int,
        status: str,
        *,
        repo_path: str | None = None,
        project_key: str | None = None,
    ) -> dict[str, Any]:
        repo_root, resolved_project_key = resolve_project_identity(self.database, repo_path=repo_path, project_key=project_key)
        self.database.upsert_project(
            resolved_project_key,
            str(repo_root),
            repo_name=repo_root.name,
        )
        pending = self.database.update_task_status(
            pending_id,
            status,
            project_key=resolved_project_key,
        )
        return {
            "project_key": resolved_project_key,
            "pending": pending,
        }

    def store_checkpoint(self, text: str, project_key: str, kind: str, source: str) -> dict[str, Any]:
        plan = create_capture_plan(text)
        plan = apply_classification_overrides(
            text,
            plan,
            {
                "intent": "general_note",
                "confidence": 0.93,
                "status": "ready",
                "normalized_summary": build_checkpoint_title(text, kind),
                "clarification_question": None,
                "domain": "Programacion",
                "project_key": project_key,
            },
        )
        plan["task"] = None
        plan["memory"] = {
            "memory_kind": "procedural" if kind in {"decision", "resolved_error", "workflow"} else "semantic",
            "title": build_checkpoint_title(text, kind),
            "summary": summarize_text(text, limit=160),
            "distilled_knowledge": text[:400],
            "domain": "Programacion",
            "scope": "project",
            "project_key": project_key,
            "importance": 3,
            "confidence": 0.93,
            "status": "ready",
        }
        result = self.database.capture(text, source, project_key, plan)
        topic_link = self.maybe_link_topic(text, result["memory_item_id"])
        result["topic_link"] = topic_link
        return result

    def maybe_link_topic(self, text: str, memory_item_id: int | None) -> dict[str, Any] | None:
        if not memory_item_id:
            return None

        lowered = text.lower()
        for topic_key, patterns in TOPIC_PATTERNS.items():
            if any(pattern in lowered for pattern in patterns):
                self.database.create_topic(topic_key, topic_key.split("/")[-1].replace("-", " ").title(), "Programacion")
                return self.database.link_to_topic(topic_key, memory_item_id=memory_item_id)
        return None

