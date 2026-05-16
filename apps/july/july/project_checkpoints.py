from __future__ import annotations

from july.project_text import summarize_text

TOPIC_PATTERNS = {
    "mcp/integration": ("mcp", "model context protocol"),
    "auth/jwt-flow": ("jwt", "token", "refresh token"),
    "excel/automation": ("excel", "spreadsheet"),
    "repo/structure": ("arquitectura", "entrypoint", "estructura"),
}

SENSITIVE_PATTERNS = (
    "api key",
    "apikey",
    "secret",
    "password",
    "token=",
    "bearer ",
    "sk-",
    "sb_publishable_",
    "anon key",
)
TENTATIVE_PATTERNS = (
    "quiz",
    "tal vez",
    "igual",
    "puede que",
    "podria",
    "podriamos",
    "maybe",
    "might",
    "draft",
    "tentative",
)
DURABLE_PATTERNS = (
    "decision",
    "decid",
    "eleg",
    "usar",
    "obligatorio",
    "siempre",
    "evitar",
    "fix",
    "solucion",
    "resuelto",
    "resolv",
    "error",
    "configur",
    "workflow",
    "mcp",
)
REUSABLE_PATTERNS = (
    "porque",
    "para ",
    "para evitar",
    "para que",
    "con ",
    "sin ",
    "como ",
)


def classify_checkpoint(text: str) -> tuple[str, str, str]:
    lowered = text.lower()
    if any(pattern in lowered for pattern in SENSITIVE_PATTERNS):
        return "ignore", "Contiene datos sensibles o credenciales. No conviene guardarlo.", "sensitive"

    tentative = any(pattern in lowered for pattern in TENTATIVE_PATTERNS)
    durable = any(pattern in lowered for pattern in DURABLE_PATTERNS)
    reusable = any(pattern in lowered for pattern in REUSABLE_PATTERNS)
    kind = detect_checkpoint_kind(lowered)

    if durable and reusable and len(text.strip()) >= 40 and not tentative:
        return "store_directly", "Parece durable, reutilizable, especifico y seguro de almacenar.", kind
    if tentative:
        return "ask_user", "Hay senal util, pero todavia suena tentativo o ambiguo.", kind
    return "ask_user", "Puede ser util, pero necesito confirmacion antes de guardarlo.", kind


def detect_checkpoint_kind(lowered: str) -> str:
    if any(token in lowered for token in ("decision", "decid", "eleg", "usar", "evitar")):
        return "decision"
    if any(token in lowered for token in ("error", "fix", "resuelto", "resolv", "solucion")):
        return "resolved_error"
    if any(token in lowered for token in ("workflow", "paso", "flujo", "script", "automat")):
        return "workflow"
    return "finding"


def build_checkpoint_title(text: str, kind: str) -> str:
    prefixes = {
        "decision": "Decision reutilizable",
        "resolved_error": "Error resuelto",
        "workflow": "Mejora de flujo",
        "finding": "Hallazgo reusable",
    }
    return f"{prefixes.get(kind, 'Hallazgo')}: {summarize_text(text, limit=80)}"


def build_improvement_title(text: str) -> str:
    clean = summarize_text(text, limit=110)
    lowered = clean.lower()
    for prefix in ("idea:", "mejora:", "posible mejora:", "incluir como posible mejora"):
        if lowered.startswith(prefix):
            clean = clean[len(prefix):].strip(" .:-")
            break
    return f"Mejora posible: {summarize_text(clean, limit=90)}"


def build_pending_title(text: str) -> str:
    clean = summarize_text(text, limit=110)
    lowered = clean.lower()
    for prefix in ("pendiente:", "por hacer:", "todo:", "tarea:"):
        if lowered.startswith(prefix):
            clean = clean[len(prefix):].strip(" .:-")
            break
    return f"Pendiente: {summarize_text(clean, limit=95)}"
