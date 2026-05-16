from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from july.project_text import summarize_text

if TYPE_CHECKING:
    from july.db import JulyDatabase

README_NAMES = ("README.md", "README.txt", "README")
OPTIONAL_DOCS = ("AGENTS.md",)
MANIFEST_FILES = (
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "Pipfile",
    "Cargo.toml",
    "go.mod",
    "composer.json",
    "Gemfile",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
)
ENTRYPOINT_FILES = (
    "main.py",
    "app.py",
    "server.py",
    "manage.py",
    "wsgi.py",
    "asgi.py",
    "index.js",
    "server.js",
    "app.js",
    "main.ts",
    "index.ts",
    "server.ts",
    "src/main.ts",
    "src/index.ts",
    "src/main.js",
    "src/index.js",
)

STACK_HINTS = {
    "python": "Python",
    "pyproject.toml": "Python",
    "requirements.txt": "Python",
    "pipfile": "Python",
    "package.json": "Node.js",
    "index.ts": "TypeScript",
    "main.ts": "TypeScript",
    "server.ts": "TypeScript",
    "cargo.toml": "Rust",
    "go.mod": "Go",
    "composer.json": "PHP",
    "gemfile": "Ruby",
    "dockerfile": "Docker",
    "docker-compose.yml": "Docker Compose",
    "docker-compose.yaml": "Docker Compose",
}

INTEGRATION_KEYWORDS = {
    "supabase": "Supabase",
    "render": "Render",
    "anthropic": "Anthropic",
    "openai": "OpenAI",
    "claude": "Anthropic",
    "ollama": "Ollama",
    "mcp": "MCP",
    "excel": "Excel",
    "google sheets": "Google Sheets",
    "stripe": "Stripe",
    "postgres": "Postgres",
    "sqlite": "SQLite",
    "docker": "Docker",
}


@dataclass(slots=True)
class RepositorySurface:
    repo_root: Path
    repo_name: str
    manifests: list[str]
    entrypoints: list[str]
    docs: list[str]
    stack: list[str]


@dataclass(slots=True)
class ProjectProfile:
    project_kind: str
    project_tags: list[str]
    preferences: dict[str, Any]


def detect_repo_root(repo_path: str | None) -> Path:
    start = Path(repo_path).expanduser().resolve() if repo_path else Path.cwd().resolve()
    current = start if start.is_dir() else start.parent

    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
        if any((candidate / name).exists() for name in README_NAMES + MANIFEST_FILES + OPTIONAL_DOCS):
            return candidate
    return current


def derive_project_key(repo_root: Path, *, explicit: str | None = None) -> str:
    value = explicit or repo_root.name
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "project"


def resolve_project_identity(
    database: JulyDatabase,
    *,
    repo_path: str | None = None,
    project_key: str | None = None,
) -> tuple[Path, str]:
    explicit_key = project_key.strip().lower() if isinstance(project_key, str) and project_key.strip() else None
    if explicit_key and not repo_path:
        existing = database.get_project(explicit_key)
        if existing is None:
            raise ValueError(
                f"Project {explicit_key} not found in the registry. Provide repo_path to register it first."
            )
        return Path(existing["repo_root"]).resolve(), explicit_key

    repo_root = detect_repo_root(repo_path)
    resolved_project_key = derive_project_key(repo_root, explicit=project_key)
    existing = database.get_project(resolved_project_key)
    if existing is not None and not repo_path:
        return Path(existing["repo_root"]).resolve(), resolved_project_key
    return repo_root, resolved_project_key


def inspect_repository_surface(repo_root: Path) -> RepositorySurface:
    names = {path.name.lower(): path.name for path in repo_root.iterdir() if path.is_file()}
    manifests = [names[name.lower()] for name in MANIFEST_FILES if name.lower() in names]
    docs = [names[name.lower()] for name in README_NAMES + OPTIONAL_DOCS if name.lower() in names]
    entrypoints = []
    for relative in ENTRYPOINT_FILES:
        candidate = repo_root / relative
        if candidate.exists():
            entrypoints.append(relative)

    entrypoint_names = [entrypoint.lower() for entrypoint in entrypoints]
    stack = sorted({hint for name, hint in STACK_HINTS.items() if name in names or name in entrypoint_names})
    return RepositorySurface(
        repo_root=repo_root,
        repo_name=repo_root.name,
        manifests=manifests,
        entrypoints=entrypoints,
        docs=docs,
        stack=stack,
    )


def analyze_repository(repo_root: Path) -> dict[str, Any]:
    surface = inspect_repository_surface(repo_root)
    profile = infer_project_profile(repo_root, surface)
    files_to_read = []
    for name in README_NAMES + OPTIONAL_DOCS + MANIFEST_FILES:
        candidate = repo_root / name
        if candidate.exists():
            files_to_read.append(candidate)
    for relative in ENTRYPOINT_FILES:
        candidate = repo_root / relative
        if candidate.exists():
            files_to_read.append(candidate)

    unique_files = []
    seen: set[Path] = set()
    for path in files_to_read:
        if path not in seen:
            unique_files.append(path)
            seen.add(path)

    file_contents = {str(path.relative_to(repo_root)): read_limited_text(path) for path in unique_files[:12]}
    combined_text = "\n".join(file_contents.values()).lower()

    package_commands = extract_package_commands(repo_root / "package.json")
    visible_commands = package_commands or infer_default_commands(surface)
    integrations = detect_integrations(combined_text)
    objective = extract_objective(file_contents)
    open_questions = build_open_questions(surface, objective, visible_commands)

    return {
        "repo_name": surface.repo_name,
        "repo_root": str(repo_root),
        "files_read": list(file_contents.keys()),
        "objective": objective,
        "stack": surface.stack or ["No detectado"],
        "commands": visible_commands,
        "integrations": integrations,
        "entrypoints": surface.entrypoints,
        "open_questions": open_questions,
        "docs": surface.docs,
        "manifests": surface.manifests,
        "project_kind": profile.project_kind,
        "project_tags": profile.project_tags,
        "preferences": profile.preferences,
    }


def read_limited_text(path: Path, limit: int = 4000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:limit]
    except OSError:
        return ""


def extract_package_commands(package_json_path: Path) -> list[str]:
    if not package_json_path.exists():
        return []
    try:
        data = json.loads(package_json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    scripts = data.get("scripts", {})
    commands = []
    for name in ("dev", "start", "build", "test", "lint"):
        if name in scripts:
            commands.append(f"npm run {name}")
    return commands


def infer_project_profile(repo_root: Path, surface: RepositorySurface) -> ProjectProfile:
    text_parts = []
    for name in README_NAMES + OPTIONAL_DOCS + MANIFEST_FILES:
        candidate = repo_root / name
        if candidate.exists():
            text_parts.append(read_limited_text(candidate, limit=2500))
    combined_text = "\n".join(text_parts).lower()
    kind = infer_project_kind(surface, combined_text)
    tags = infer_project_tags(surface, combined_text, kind)
    return ProjectProfile(
        project_kind=kind,
        project_tags=tags,
        preferences=default_preferences_for_kind(kind, tags),
    )


def infer_project_kind(surface: RepositorySurface, text: str) -> str:
    has_package = "package.json" in surface.manifests
    has_python = any(item in surface.manifests for item in ("pyproject.toml", "requirements.txt", "Pipfile"))
    has_docker = any(item.lower().startswith("docker") for item in surface.manifests)
    entrypoints = " ".join(surface.entrypoints).lower()

    if any(token in text for token in ("landing", "pagina web", "página web", "web de cliente", "sitio web", "seo local")):
        return "website"
    if any(token in text for token in ("mobile app", "android", "ios", "react native", "flutter")):
        return "mobile_app"
    if any(token in text for token in ("desktop app", "electron", "tauri")):
        return "desktop_app"
    if any(token in text for token in ("cli", "command line", "terminal", "stdio")):
        return "cli_tool"
    if has_package and any(item in entrypoints for item in ("src/main", "src/index", "index.ts", "main.ts")):
        return "web_app"
    if any(token in text for token in ("api", "backend", "fastapi", "express", "server")) or has_docker:
        return "backend"
    if any(token in text for token in ("automatizacion", "automatización", "workflow", "script")):
        return "automation"
    if has_python and not has_package:
        return "software"
    if surface.docs and not surface.manifests:
        return "knowledge_base"
    return "unknown"


def infer_project_tags(surface: RepositorySurface, text: str, kind: str) -> list[str]:
    tags = {kind}
    for keyword, label in INTEGRATION_KEYWORDS.items():
        if keyword in text:
            tags.add(label.lower().replace(" ", "-"))
    stack_tags = {item.lower().replace(".", "").replace(" ", "-") for item in surface.stack}
    tags.update(stack_tags)
    if "cliente" in text or "client" in text:
        tags.add("cliente")
    if "landing" in text:
        tags.add("landing")
    if "ecommerce" in text or "tienda" in text:
        tags.add("ecommerce")
    if "supabase" in text:
        tags.add("supabase")
    if "render" in text:
        tags.add("render")
    if "seo" in text:
        tags.add("seo")
    return sorted(tag for tag in tags if tag and tag != "unknown")


def default_preferences_for_kind(kind: str, tags: list[str]) -> dict[str, Any]:
    is_website = kind in {"website", "web_app"} or "landing" in tags or "seo" in tags
    return {
        "ask_before_save": True,
        "auto_session_summary": True,
        "suggest_caveman": True,
        "suggest_design_extract": is_website,
        "suggest_codeburn": kind in {"web_app", "backend", "software", "cli_tool"},
        "open_cockpit": False,
    }


def infer_default_commands(surface: RepositorySurface) -> list[str]:
    commands = []
    if "package.json" in surface.manifests:
        commands.extend(["npm install", "npm run dev"])
    if any(item in surface.manifests for item in ("pyproject.toml", "requirements.txt", "Pipfile")):
        commands.extend(["python -m venv .venv", "python -m pytest"])
    return commands or ["Revisar README para comandos concretos"]


def detect_integrations(text: str) -> list[str]:
    return sorted({label for keyword, label in INTEGRATION_KEYWORDS.items() if keyword in text})


def extract_objective(file_contents: dict[str, str]) -> str:
    for name, content in file_contents.items():
        if name.lower().startswith("readme") and content.strip():
            lines = [line.strip(" #*-") for line in content.splitlines() if line.strip()]
            for line in lines:
                if len(line) > 20:
                    return summarize_text(line, limit=220)
    return "No hay una descripcion explicita; conviene confirmar el objetivo del repo."


def build_open_questions(surface: RepositorySurface, objective: str, commands: list[str]) -> list[str]:
    questions = []
    if not surface.docs:
        questions.append("Falta README o documentacion base visible.")
    if not surface.entrypoints:
        questions.append("No he detectado entrypoints obvios en superficie.")
    if objective.startswith("No hay una descripcion"):
        questions.append("Conviene confirmar el objetivo funcional del proyecto.")
    if not commands:
        questions.append("No hay comandos utiles detectados todavia.")
    return questions
