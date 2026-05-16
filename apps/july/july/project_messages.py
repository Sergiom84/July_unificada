from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from july.project_surface import RepositorySurface


def assess_project_state(project_ctx: dict[str, list[Any]], sessions: list[dict[str, Any]]) -> str:
    has_ready_memory = any(row["status"] == "ready" for row in project_ctx["memory"])
    has_session_summary = any(
        (session.get("summary") or session.get("discoveries") or session.get("next_steps")) for session in sessions
    )
    has_any_context = any(project_ctx[section] for section in ("inbox", "tasks", "memory", "improvements")) or bool(sessions)

    if has_ready_memory and has_session_summary:
        return "known"
    if has_any_context:
        return "partial"
    return "new"


def build_context_summary(
    project_key: str,
    project_ctx: dict[str, list[Any]],
    sessions: list[dict[str, Any]],
    surface: RepositorySurface,
) -> str:
    if not any(project_ctx[section] for section in ("inbox", "tasks", "memory", "improvements")) and not sessions:
        stack = ", ".join(surface.stack) if surface.stack else "stack no detectado"
        return f"No tengo contexto persistido de {project_key} todavia. En superficie parece un repo de {stack}."

    latest_memory = project_ctx["memory"][0]["summary"] if project_ctx["memory"] else None
    latest_improvement = project_ctx["improvements"][0]["title"] if project_ctx["improvements"] else None
    latest_session = sessions[0] if sessions else None
    parts = [f"July ya tiene algo de contexto para {project_key}."]
    if latest_memory:
        parts.append(f"Ultima memoria util: {latest_memory}")
    if latest_improvement:
        parts.append(f"Mejora pendiente: {latest_improvement}")
    if latest_session and latest_session.get("summary"):
        parts.append(f"Ultima sesion: {latest_session['summary']}")
    if latest_session and latest_session.get("next_steps"):
        parts.append(f"Siguiente paso conocido: {latest_session['next_steps']}")
    return " ".join(parts)


def build_recall_query(project_key: str, context_summary: str, surface: RepositorySurface) -> str:
    terms = [project_key, context_summary, surface.repo_name]
    terms.extend(surface.stack[:3])
    terms.extend(surface.manifests[:2])
    return " ".join(term for term in terms if term)


def build_entry_message(project_state: str, surface: RepositorySurface, context_summary: str) -> str:
    if project_state == "new":
        stack = ", ".join(surface.stack) if surface.stack else "stack no detectado"
        return (
            f"Proyecto nuevo para July. Veo un repo llamado {surface.repo_name} "
            f"y en superficie parece usar {stack}. "
            "Si se ejecuta analyze_now, July leera documentacion y entrypoints en modo solo lectura "
            "para dejar una primera foto util."
        )
    if project_state == "known":
        return f"Proyecto conocido en July. {context_summary}"
    return (
        f"Contexto parcial de {surface.repo_name}. "
        f"{context_summary} Si quieres, hago un refresh selectivo antes de continuar."
    )


def build_permission_request(project_state: str, surface: RepositorySurface) -> dict[str, Any] | None:
    if project_state != "new":
        return None
    return {
        "action": "analyze_now",
        "mode": "read_only",
        "message": (
            "Voy a leer README, manifiestos y entrypoints visibles para darte mejores practicas "
            "y guardar una primera foto del proyecto. Quieres que lo haga ahora?"
        ),
        "files_hint": surface.docs + surface.manifests + surface.entrypoints[:4],
    }


def recommended_action_for_state(project_state: str) -> str:
    if project_state == "new":
        return "analyze_now"
    if project_state == "known":
        return "resume_context"
    return "refresh_context"


def build_entry_options(project_state: str) -> list[dict[str, str]]:
    if project_state == "new":
        return [
            {"action": "analyze_now", "label": "Si, analiza ahora"},
            {"action": "help", "label": "Ayuda"},
            {"action": "wait", "label": "Prefiero esperar"},
            {"action": "do_nothing", "label": "No hagas nada"},
        ]
    if project_state == "known":
        return [
            {"action": "resume_context", "label": "Resume el contexto"},
            {"action": "help", "label": "Ayuda"},
            {"action": "refresh_context", "label": "Refresca el contexto"},
            {"action": "continue_without_context", "label": "Seguimos sin refresco"},
        ]
    return [
        {"action": "refresh_context", "label": "Refresca el contexto"},
        {"action": "help", "label": "Ayuda"},
        {"action": "analyze_now", "label": "Haz onboarding completo"},
        {"action": "continue_without_context", "label": "Seguimos asi"},
    ]


def build_snapshot_text(project_key: str, analysis: dict[str, Any]) -> str:
    return (
        f"Onboarding inicial del proyecto {project_key}.\n"
        f"Objetivo visible: {analysis['objective']}\n"
        f"Tipo de proyecto: {analysis['project_kind']}\n"
        f"Tags: {', '.join(analysis['project_tags']) or 'ninguno'}\n"
        f"Stack visible: {', '.join(analysis['stack'])}\n"
        f"Comandos utiles: {', '.join(analysis['commands'])}\n"
        f"Integraciones importantes: {', '.join(analysis['integrations']) or 'ninguna detectada'}\n"
        f"Entrypoints visibles: {', '.join(analysis['entrypoints']) or 'ninguno detectado'}\n"
        f"Dudas abiertas: {', '.join(analysis['open_questions']) or 'ninguna critica'}"
    )


def build_snapshot_summary(analysis: dict[str, Any]) -> str:
    return (
        f"Objetivo: {analysis['objective']} "
        f"Tipo: {analysis['project_kind']}. "
        f"Stack: {', '.join(analysis['stack'])}. "
        f"Integraciones: {', '.join(analysis['integrations']) or 'ninguna detectada'}. "
        f"Entrypoints: {', '.join(analysis['entrypoints']) or 'ninguno detectado'}."
    )


def build_distilled_knowledge(analysis: dict[str, Any]) -> str:
    return (
        f"El proyecto parece orientado a {analysis['objective']} "
        f"y July lo clasifica como {analysis['project_kind']} "
        f"y trabaja con {', '.join(analysis['stack'])}. "
        f"Los comandos mas utiles detectados ahora son {', '.join(analysis['commands'])}. "
        f"Las dudas abiertas principales son: {', '.join(analysis['open_questions']) or 'ninguna critica'}."
    )


def suggest_next_step(analysis: dict[str, Any]) -> str:
    if analysis["open_questions"]:
        return analysis["open_questions"][0]
    if analysis["commands"]:
        return f"Probar el flujo principal con {analysis['commands'][0]}."
    return "Confirmar el objetivo y el siguiente bloque de trabajo con el usuario."


def build_session_key(project_key: str, *, prefix: str) -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S%f")
    return f"{prefix}-{project_key}-{timestamp}"


def compare_repository_with_context(analysis: dict[str, Any], context_summary: str) -> dict[str, Any]:
    lowered = context_summary.lower()
    changes = []
    for item in analysis["stack"]:
        if item.lower() not in lowered:
            changes.append(f"Stack visible no mencionado antes: {item}")
    for item in analysis["integrations"]:
        if item.lower() not in lowered:
            changes.append(f"Integracion visible no mencionada antes: {item}")
    for item in analysis["entrypoints"]:
        if item.lower() not in lowered:
            changes.append(f"Entrypoint visible no mencionado antes: {item}")
    if not changes:
        changes.append("No veo diferencias fuertes en stack, integraciones o entrypoints frente al contexto previo.")
    return {"changes": changes, "summary": " ".join(changes[:3])}


def build_project_help(entry: dict[str, Any]) -> dict[str, Any]:
    profile = entry["profile"]
    surface = entry["surface"]
    knows = [
        f"Estado del proyecto en July: {entry['project_state']}",
        f"Tipo detectado: {profile['project_kind']}",
        f"Tags: {', '.join(profile['project_tags']) or 'ninguno'}",
        f"Stack visible: {', '.join(surface['stack']) or 'no detectado'}",
        f"Documentos visibles: {', '.join(surface['docs']) or 'ninguno'}",
        entry["context_summary"],
    ]
    unknowns = []
    if not surface["entrypoints"]:
        unknowns.append("No tengo entrypoints claros todavia.")
    if not surface["docs"]:
        unknowns.append("No veo README o documentacion base.")
    if entry["project_state"] == "new":
        unknowns.append("No hay memoria persistida suficiente para retomar este proyecto sin onboarding.")
    if not unknowns:
        unknowns.append("No veo huecos criticos en la foto superficial; el siguiente riesgo es staleness del contexto.")

    can_do = [
        "Hacer onboarding read-only del repo.",
        "Resumir contexto previo y siguientes pasos.",
        "Guardar decisiones, hallazgos y errores resueltos.",
        "Guardar ideas o posibles mejoras para revisarlas mas adelante.",
        "Guardar pendientes por hacer y marcarlos como done cuando se completen.",
        "Sugerir skills registradas cuando el contexto encaje con una herramienta reutilizable.",
        "Abrir o enlazar el cockpit local del proyecto.",
    ]
    if profile["preferences"].get("suggest_caveman"):
        can_do.append("Sugerir Caveman para ahorrar salida cuando haya mucha conversacion.")
    if profile["preferences"].get("suggest_design_extract"):
        can_do.append("Sugerir Design Extract cuando el trabajo sea visual o de web.")
    if profile["preferences"].get("suggest_codeburn"):
        can_do.append("Sugerir CodeBurn para revisar consumo de agentes.")

    return {
        "message": "Ayuda de July: esto es lo que se, lo que falta y lo que puedo hacer.",
        "knows": knows,
        "unknowns": unknowns,
        "can_do": can_do,
        "preferences": profile["preferences"],
    }


def extract_next_step(recall: dict[str, Any], context_summary: str) -> str:
    related_sessions = recall.get("related_sessions", [])
    if related_sessions:
        next_steps = related_sessions[0].get("next_steps")
        if next_steps:
            return next_steps
    return context_summary


def build_copilot_hint(developer_level: str, architect: dict[str, Any]) -> str:
    smells_count = architect.get("code_smells_count", 0)
    insights = architect.get("insights", [])
    questions = architect.get("proactive_questions", [])
    suggestions = architect.get("suggestions", [])

    if developer_level == "junior":
        parts = []
        if insights:
            best = insights[0]
            parts.append(
                f"Tu proyecto sigue un patron de {best['pattern']}. "
                f"{best['suggestion']}"
            )
        if smells_count > 0:
            parts.append(
                f"He encontrado {smells_count} puntos de mejora en el codigo. "
                "Te los explico uno a uno si quieres."
            )
        if suggestions:
            parts.append(f"Consejo: {suggestions[0]}")
        return " ".join(parts) if parts else "Proyecto analizado. Preguntame lo que necesites."

    if developer_level == "mid":
        parts = []
        if insights:
            for insight in insights[:2]:
                parts.append(f"[{insight['pattern']}] {insight['detail']}")
        if smells_count > 3:
            parts.append(f"{smells_count} code smells detectados. Los mas criticos primero?")
        if questions:
            parts.append(questions[0])
        return " ".join(parts) if parts else "Analisis completo. Dime en que quieres profundizar."

    parts = []
    if smells_count > 5:
        parts.append(f"{smells_count} smells. Revisa los criticos.")
    if insights:
        for insight in insights:
            if insight["confidence"] < 0.8:
                parts.append(f"Patron ambiguo: {insight['pattern']} ({insight['confidence']:.0%})")
    if not parts:
        parts.append("Codigo limpio. Sin flags criticos.")
    return " ".join(parts)
