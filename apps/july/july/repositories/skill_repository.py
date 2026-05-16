from __future__ import annotations

import json
import sqlite3

from july.storage.utils import (
    normalize_json_array,
    parse_json_array,
    skill_reference_tokens,
    utc_now,
)

SKILL_REFERENCE_STATUSES = {"active", "inactive"}


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
        if not query_tokens:
            return []

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
            project_match = bool(project_key and project_key in project_keys)
            if not overlap and not project_match:
                continue

            score = (len(overlap) * 2) + (len(domain_hits) * 3)
            if project_match:
                score += 8
            elif project_keys:
                score -= 1
            else:
                score += 1

            if score <= 3:
                continue

            if project_match:
                reason = f"Registrada para este proyecto; coincide con: {', '.join(overlap[:5]) or project_key}"
            elif domain_hits:
                reason = f"Coincide con dominios: {', '.join(domain_hits[:5])}"
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

        suggestions.sort(key=lambda suggestion: suggestion["score"], reverse=True)
        return suggestions[:limit]
