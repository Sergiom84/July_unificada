from __future__ import annotations

from typing import Any


def build_best_practice_suggestions(
    *,
    entry: dict[str, Any],
    active_session: dict[str, Any] | None,
    pending_tasks: list[dict[str, Any]],
    pending_improvements: list[dict[str, Any]],
    recent_memory: list[dict[str, Any]],
    sessions: list[dict[str, Any]],
) -> list[dict[str, str]]:
    suggestions: list[dict[str, str]] = []
    state = entry["project_state"]

    if state == "new":
        suggestions.append(
            {
                "title": "Haz una revision inicial",
                "detail": "El proyecto no tiene contexto util todavia. Ejecuta analyze_now para dejar una primera foto fiable.",
                "action_hint": "analyze_now",
            }
        )
    elif state == "partial":
        suggestions.append(
            {
                "title": "Refresca el contexto parcial",
                "detail": "Hay memoria suelta o sesiones incompletas. Un refresh selectivo aclarara el punto real del proyecto.",
                "action_hint": "refresh_context",
            }
        )
    else:
        suggestions.append(
            {
                "title": "Recupera el contexto antes de tocar nada",
                "detail": "El proyecto ya tiene memoria util. Resume primero el contexto para no repetir trabajo.",
                "action_hint": "resume_context",
            }
        )

    if active_session is None:
        suggestions.append(
            {
                "title": "Abre una sesion antes de iterar",
                "detail": "Si vas a tomar varias decisiones, deja una sesion activa para poder cerrarla con resumen y siguientes pasos.",
                "action_hint": "session_start",
            }
        )
    elif active_session["status"] == "active":
        suggestions.append(
            {
                "title": "No dejes la sesion ciega",
                "detail": "Hay una sesion activa sin cierre. Resume lo hecho y cierrala cuando termines.",
                "action_hint": "session_summary",
            }
        )

    if pending_tasks:
        suggestions.append(
            {
                "title": "Ordena los pendientes abiertos",
                "detail": f"Hay {len(pending_tasks)} pendientes sin cerrar. Conviene moverlos a in_progress o done para que el cockpit refleje la realidad.",
                "action_hint": "task_review",
            }
        )

    if pending_improvements:
        suggestions.append(
            {
                "title": "Revisa mejoras pendientes",
                "detail": f"Hay {len(pending_improvements)} ideas de mejora abiertas. Conviene convertir las utiles en tareas o descartarlas.",
                "action_hint": "improvement_review",
            }
        )

    if not recent_memory:
        suggestions.append(
            {
                "title": "Guarda decisiones y hallazgos durables",
                "detail": "El proyecto tiene poca memoria reutilizable. Registra decisiones y hallazgos para evitar regresiones de contexto.",
                "action_hint": "save_decision",
            }
        )
    elif sessions and not any(session.get("next_steps") for session in sessions):
        suggestions.append(
            {
                "title": "Deja siguiente paso explicito",
                "detail": "Hay sesiones previas, pero falta una cadena clara de siguientes pasos reutilizables.",
                "action_hint": "session_summary",
            }
        )

    return suggestions


def rows_to_dicts(result: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    return {
        section: [dict(row) for row in rows]
        for section, rows in result.items()
    }


def build_activity_feed(
    *,
    memory_items: list[dict[str, Any]],
    inbox_items: list[dict[str, Any]],
    sessions: list[dict[str, Any]],
    tasks: list[dict[str, Any]],
    improvements: list[dict[str, Any]],
    findings: list[dict[str, Any]],
) -> list[dict[str, str]]:
    events: list[dict[str, str]] = []

    for memory in memory_items:
        if memory["title"].lower().startswith("hallazgo"):
            continue
        events.append(
            {
                "kind": "memory",
                "title": memory["title"],
                "detail": memory.get("summary") or memory.get("memory_kind", "Memoria de proyecto"),
                "timestamp": memory.get("created_at") or "",
                "label": memory.get("memory_kind", "memory"),
            }
        )

    for finding in findings:
        events.append(
            {
                "kind": "finding",
                "title": finding["title"],
                "detail": finding.get("summary") or "Hallazgo reciente del proyecto",
                "timestamp": finding.get("created_at") or "",
                "label": "finding",
            }
        )

    for session in sessions:
        events.append(
            {
                "kind": "session",
                "title": session["session_key"],
                "detail": session.get("summary") or session.get("goal") or "Sesion sin resumen todavia",
                "timestamp": session.get("ended_at") or session.get("started_at") or "",
                "label": session.get("status", "session"),
            }
        )

    for task in tasks:
        events.append(
            {
                "kind": "task",
                "title": task["title"],
                "detail": f"Pendiente en estado {task.get('status', 'pending')}",
                "timestamp": task.get("created_at") or "",
                "label": task.get("status", "task"),
            }
        )

    for improvement in improvements:
        events.append(
            {
                "kind": "improvement",
                "title": improvement["title"],
                "detail": f"Mejora en estado {improvement.get('status', 'open')}",
                "timestamp": improvement.get("updated_at") or improvement.get("created_at") or "",
                "label": improvement.get("priority", "normal"),
            }
        )

    for inbox in inbox_items:
        events.append(
            {
                "kind": "inbox",
                "title": inbox.get("normalized_summary") or "Entrada capturada",
                "detail": inbox.get("detected_intent") or "Input libre del proyecto",
                "timestamp": inbox.get("created_at") or "",
                "label": inbox.get("status", "inbox"),
            }
        )

    events.sort(key=lambda item: item["timestamp"] or "", reverse=True)
    return events[:12]

