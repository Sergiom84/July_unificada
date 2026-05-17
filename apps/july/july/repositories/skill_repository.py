from __future__ import annotations

import json
import re
import sqlite3

from july.skill_registry import discover_local_skill_commands
from july.storage.utils import (
    normalize_json_array,
    parse_json_array,
    skill_reference_tokens,
    utc_now,
)

SKILL_REFERENCE_STATUSES = {"active", "inactive"}
CORE_JULY_TRIGGER_RE = re.compile(
    r"\b(july|memoria|contexto|sesi[oó]n|sesiones|pendiente|pendientes|mejora|mejoras|project[-_ ]?entry)\b",
    re.IGNORECASE,
)
CORE_JULY_COMMAND_ORDER = ("july", "july-inicio", "pendientes", "mejoras")
PROJECT_KIND_BOOSTS = {
    "mobile_app": {
        "flutter": 2.0,
        "supabase": 2.0,
        "browser": 2.0,
        "release": 1.5,
        "release-smoke": 2.0,
    },
    "web_app": {
        "browser": 1.5,
        "visual-copilot": 1.5,
        "designlang": 1.5,
        "design-extract": 1.5,
    },
    "website": {
        "browser": 1.5,
        "visual-copilot": 1.5,
        "designlang": 1.5,
        "design-extract": 1.5,
    },
    "automation": {
        "caveman": 1.5,
        "python": 1.5,
    },
    "cli_tool": {
        "caveman": 1.5,
        "python": 1.5,
    },
    "software": {
        "caveman": 1.5,
        "python": 1.5,
    },
}


class SkillRepository:
    def __init__(self, connection_factory):
        self.connection = connection_factory

    def upsert_skill_reference(
        self,
        *,
        skill_name: str,
        description: str,
        source_path: str | None = None,
        trigger_text: str | None = None,
        display_name: str | None = None,
        domains: list[str] | tuple[str, ...] | None = None,
        project_keys: list[str] | tuple[str, ...] | None = None,
        status: str = "active",
    ) -> dict:
        skill_name = skill_name.strip()
        description = description.strip()
        trigger_text = (trigger_text or description).strip()
        display_name = (display_name or skill_name).strip()
        if not skill_name:
            raise ValueError("skill_name is required")
        if not description:
            raise ValueError("description is required")
        if status not in SKILL_REFERENCE_STATUSES:
            raise ValueError(f"Unsupported skill reference status: {status}")

        timestamp = utc_now()
        domains_json = json.dumps(normalize_json_array(domains), ensure_ascii=True)
        project_keys_json = json.dumps(normalize_json_array(project_keys), ensure_ascii=True)
        with self.connection() as conn:
            existing = conn.execute(
                "SELECT id FROM skill_references WHERE skill_name = ?",
                (skill_name,),
            ).fetchone()
            if existing:
                conn.execute(
                    """
                    UPDATE skill_references
                    SET display_name = ?, description = ?, source_path = ?, trigger_text = ?,
                        domains_json = ?, project_keys_json = ?, status = ?, updated_at = ?
                    WHERE skill_name = ?
                    """,
                    (
                        display_name, description, source_path, trigger_text,
                        domains_json, project_keys_json, status, timestamp, skill_name,
                    ),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO skill_references (
                        skill_name, display_name, description, source_path, trigger_text,
                        domains_json, project_keys_json, status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        skill_name, display_name, description, source_path, trigger_text,
                        domains_json, project_keys_json, status, timestamp, timestamp,
                    ),
                )
            row = conn.execute(
                "SELECT * FROM skill_references WHERE skill_name = ?",
                (skill_name,),
            ).fetchone()
            return dict(row)

    def list_skill_references(
        self,
        *,
        status: str | None = "active",
        include_inactive: bool = False,
        include_trigger: bool = False,
        limit: int = 20,
    ) -> list[sqlite3.Row]:
        if status and status not in SKILL_REFERENCE_STATUSES:
            raise ValueError(f"Unsupported skill reference status: {status}")
        columns = (
            "id, skill_name, display_name, description, source_path, "
            f"{'trigger_text, ' if include_trigger else ''}"
            "domains_json, project_keys_json, status, created_at, updated_at"
        )
        with self.connection() as conn:
            if include_inactive:
                return conn.execute(
                    f"""
                    SELECT {columns}
                    FROM skill_references
                    ORDER BY updated_at DESC, id DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
            return conn.execute(
                f"""
                SELECT {columns}
                FROM skill_references
                WHERE status = ?
                ORDER BY updated_at DESC, id DESC
                LIMIT ?
                """,
                (status or "active", limit),
            ).fetchall()

    def suggest_skill_references(
        self,
        text: str,
        *,
        project_key: str | None = None,
        limit: int = 5,
    ) -> list[dict]:
        query_tokens = skill_reference_tokens(text)
        core_suggestions = self.core_july_suggestions(text)
        if not query_tokens and not core_suggestions:
            return []

        project_profile = self.get_project_profile(project_key)
        suggestions: list[dict] = []
        for row in self.list_skill_references(limit=200, include_trigger=True):
            item = dict(row)
            domains = parse_json_array(item.get("domains_json"))
            project_keys = parse_json_array(item.get("project_keys_json"))
            haystack = " ".join(
                [
                    item["skill_name"],
                    item["display_name"],
                    item["description"],
                    item.get("source_path") or "",
                    " ".join(domains),
                ]
            )
            haystack = f"{haystack} {item.get('trigger_text') or ''}"

            skill_tokens = skill_reference_tokens(haystack)
            overlap = sorted(query_tokens & skill_tokens)
            domain_hits = sorted(query_tokens & skill_reference_tokens(" ".join(domains)))
            context_boost = self.project_context_boost(project_profile, skill_tokens, domains, item["skill_name"])
            project_match = bool(project_key and project_key in project_keys)
            if not overlap and not project_match and context_boost <= 0:
                continue

            score = (len(overlap) * 2) + (len(domain_hits) * 3) + context_boost
            if project_match:
                score += 8
            elif project_keys:
                score -= 1
            else:
                score += 1

            if score <= 3 and context_boost <= 0:
                continue

            if project_match:
                reason = f"Registrada para este proyecto; coincide con: {', '.join(overlap[:5]) or project_key}"
            elif domain_hits:
                reason = f"Coincide con dominios: {', '.join(domain_hits[:5])}"
            elif context_boost > 0:
                reason = f"Encaja con el tipo de proyecto ({project_profile.get('project_kind')})"
            else:
                reason = f"Coincide con: {', '.join(overlap[:5])}"

            suggestions.append({
                "type": "skill_reference",
                "skill_name": item["skill_name"],
                "display_name": item["display_name"],
                "description": item["description"],
                "source_path": item.get("source_path"),
                "domains": domains,
                "project_keys": project_keys,
                "score": score,
                "reason": reason,
            })

        suggestions.sort(key=lambda suggestion: (-suggestion["score"], suggestion["skill_name"]))
        return merge_skill_suggestions(core_suggestions, suggestions, limit)

    def get_project_profile(self, project_key: str | None) -> dict:
        if not project_key:
            return {"project_kind": None, "project_tags": []}
        with self.connection() as conn:
            row = conn.execute(
                "SELECT project_kind, project_tags_json FROM projects WHERE project_key = ?",
                (project_key,),
            ).fetchone()
        if row is None:
            return {"project_kind": None, "project_tags": []}
        return {
            "project_kind": row["project_kind"],
            "project_tags": parse_json_array(row["project_tags_json"]),
        }

    def project_context_boost(
        self,
        project_profile: dict,
        skill_tokens: set[str],
        domains: list[str],
        skill_name: str,
    ) -> float:
        project_kind = project_profile.get("project_kind")
        boost_map = PROJECT_KIND_BOOSTS.get(project_kind or "", {})
        if not boost_map:
            return 0.0
        searchable = set(skill_tokens)
        searchable.update(skill_reference_tokens(" ".join(domains)))
        searchable.update(skill_reference_tokens(skill_name))
        return sum(weight for token, weight in boost_map.items() if token in searchable)

    def core_july_suggestions(self, text: str) -> list[dict]:
        if not CORE_JULY_TRIGGER_RE.search(text):
            return []
        commands = {
            item["skill_name"]: item
            for item in discover_local_skill_commands(limit=100)
            if item.get("skill_name") in CORE_JULY_COMMAND_ORDER
        }
        suggestions: list[dict] = []
        for index, skill_name in enumerate(CORE_JULY_COMMAND_ORDER):
            item = commands.get(skill_name)
            if item is None:
                continue
            suggestions.append({
                **item,
                "score": 1000 - index,
                "reason": "Comando core de July para memoria, contexto, sesiones, pendientes o mejoras.",
                "is_core": True,
            })
        return suggestions


def merge_skill_suggestions(core: list[dict], ranked: list[dict], limit: int) -> list[dict]:
    merged: list[dict] = []
    seen: set[str] = set()
    for suggestion in [*core, *ranked]:
        name = suggestion.get("skill_name")
        if not name or name in seen:
            continue
        seen.add(name)
        merged.append(suggestion)
        if len(merged) >= limit:
            break
    return merged
