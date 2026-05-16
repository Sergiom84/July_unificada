from __future__ import annotations

import json
from typing import Any

from july.analyzer import analyze_codebase
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
from july.project_messages import (
    assess_project_state,
    build_context_summary,
    build_copilot_hint,
    build_distilled_knowledge,
    build_entry_message,
    build_entry_options,
    build_permission_request,
    build_project_help,
    build_recall_query,
    build_session_key,
    build_snapshot_summary,
    build_snapshot_text,
    compare_repository_with_context,
    extract_next_step,
    recommended_action_for_state,
    suggest_next_step,
)
from july.project_surface import (
    analyze_repository,
    derive_project_key,
    detect_repo_root,
    infer_project_profile,
    inspect_repository_surface,
    resolve_project_identity,
)
from july.project_text import summarize_text


class ProjectConversationService:
    def __init__(self, database: JulyDatabase) -> None:
        self.database = database

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
        topic_link = self._maybe_link_topic(snapshot_text, capture_result["memory_item_id"])

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
        entry = self.project_entry(repo_path=str(repo_root), project_key=resolved_project_key)

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
            stored = self._store_checkpoint(text, resolved_project_key, kind, source)

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
        stored = self._store_checkpoint(text, resolved_project_key, "decision", source)
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
        stored = self._store_checkpoint(text, resolved_project_key, "finding", source)
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

    def _store_checkpoint(self, text: str, project_key: str, kind: str, source: str) -> dict[str, Any]:
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
        topic_link = self._maybe_link_topic(text, result["memory_item_id"])
        result["topic_link"] = topic_link
        return result

    def _maybe_link_topic(self, text: str, memory_item_id: int | None) -> dict[str, Any] | None:
        if not memory_item_id:
            return None

        lowered = text.lower()
        for topic_key, patterns in TOPIC_PATTERNS.items():
            if any(pattern in lowered for pattern in patterns):
                self.database.create_topic(topic_key, topic_key.split("/")[-1].replace("-", " ").title(), "Programacion")
                return self.database.link_to_topic(topic_key, memory_item_id=memory_item_id)
        return None
