from __future__ import annotations

from typing import Any

from july.external_refs import fetch_reference_page
from july.mcp_utils import ToolSpec, require_string, string_list
from july.skill_registry import discover_local_skill_commands, load_skill_reference
from july.url_fetcher import fetch_url_metadata


class ReferenceSkillToolHandlers:
    def tool_save_model_contribution(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return self.database.save_model_contribution(
            model_name=require_string(arguments, "model_name"),
            contribution_type=require_string(arguments, "contribution_type"),
            title=require_string(arguments, "title"),
            content=require_string(arguments, "content"),
            project_key=arguments.get("project_key"),
            domain=arguments.get("domain"),
            adopted=bool(arguments.get("adopted", False)),
            notes=arguments.get("notes"),
        )

    def tool_fetch_url(self, arguments: dict[str, Any]) -> dict[str, Any]:
        url = require_string(arguments, "url")
        artifact_id = arguments.get("artifact_id")
        meta = fetch_url_metadata(url)
        db_result = self.database.save_url_metadata(
            url,
            artifact_id=artifact_id,
            **{key: value for key, value in meta.items() if key not in ("url", "fetch_status")},
            fetch_status=meta["fetch_status"],
        )
        return {**meta, **db_result}

    def tool_fetch_reference(self, arguments: dict[str, Any]) -> dict[str, Any]:
        source_key = require_string(arguments, "source_key")
        return fetch_reference_page(source_key)

    def tool_skill_register(self, arguments: dict[str, Any]) -> dict[str, Any]:
        draft = load_skill_reference(require_string(arguments, "path"))
        registered = self.database.upsert_skill_reference(
            skill_name=arguments.get("name") or draft.skill_name,
            display_name=arguments.get("name") or draft.display_name,
            description=arguments.get("description") or draft.description,
            source_path=draft.source_path,
            trigger_text=arguments.get("trigger_text") or draft.trigger_text,
            domains=string_list(arguments.get("domains")),
            project_keys=string_list(arguments.get("project_keys")),
            status=arguments.get("status", "active"),
        )
        return {"skill_reference": registered}

    def tool_skill_references(self, arguments: dict[str, Any]) -> dict[str, Any]:
        limit = int(arguments.get("limit", 20))
        include_local = bool(arguments.get("include_local_commands", True))
        return {
            "skills": [
                dict(row) for row in self.database.list_skill_references(
                    status=arguments.get("status", "active"),
                    include_inactive=bool(arguments.get("include_inactive", False)),
                    limit=limit,
                )
            ],
            "local_commands": discover_local_skill_commands(limit=limit) if include_local else [],
        }

    def tool_skill_suggest(self, arguments: dict[str, Any]) -> dict[str, Any]:
        limit = int(arguments.get("limit", 5))
        return {
            "skill_suggestions": self.database.suggest_skill_references(
                require_string(arguments, "text"),
                project_key=arguments.get("project_key"),
                limit=limit,
            )
        }


def build_reference_skill_tools(server) -> dict[str, ToolSpec]:
    return {
        "save_model_contribution": ToolSpec(
            name="save_model_contribution",
            title="Save Model Contribution",
            description="Record a contribution from an AI model for traceability.",
            input_schema={
                "type": "object",
                "properties": {
                    "model_name": {"type": "string"},
                    "contribution_type": {"type": "string"},
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                    "project_key": {"type": "string"},
                    "domain": {"type": "string"},
                    "adopted": {"type": "boolean"},
                    "notes": {"type": "string"},
                },
                "required": ["model_name", "contribution_type", "title", "content"],
            },
            handler=server.tool_save_model_contribution,
        ),
        "fetch_url": ToolSpec(
            name="fetch_url",
            title="Fetch URL",
            description="Fetch metadata for a URL and save it in July.",
            input_schema={
                "type": "object",
                "properties": {"url": {"type": "string"}, "artifact_id": {"type": "integer"}},
                "required": ["url"],
            },
            handler=server.tool_fetch_url,
        ),
        "fetch_reference": ToolSpec(
            name="fetch_reference",
            title="Fetch Reference",
            description="Fetch a known external reference source such as skills.sh or agents.md.",
            input_schema={
                "type": "object",
                "properties": {"source_key": {"type": "string", "enum": ["skills.sh", "agents.md"]}},
                "required": ["source_key"],
            },
            handler=server.tool_fetch_reference,
        ),
        "skill_register": ToolSpec(
            name="skill_register",
            title="Register Skill Reference",
            description="Register a local .skill archive, skill directory, or SKILL.md as a reusable July skill reference.",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "trigger_text": {"type": "string"},
                    "domains": {"type": "array", "items": {"type": "string"}},
                    "project_keys": {"type": "array", "items": {"type": "string"}},
                    "status": {"type": "string", "enum": ["active", "inactive"]},
                },
                "required": ["path"],
            },
            handler=server.tool_skill_register,
        ),
        "skill_references": ToolSpec(
            name="skill_references",
            title="Skill References",
            description="List registered skill references and optionally local July commands.",
            input_schema={
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["active", "inactive"]},
                    "include_inactive": {"type": "boolean"},
                    "include_local_commands": {"type": "boolean"},
                    "limit": {"type": "integer"},
                },
            },
            handler=server.tool_skill_references,
        ),
        "skill_suggest": ToolSpec(
            name="skill_suggest",
            title="Suggest Skills",
            description="Suggest registered skills that match a text and optional project key.",
            input_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "project_key": {"type": "string"},
                    "limit": {"type": "integer"},
                },
                "required": ["text"],
            },
            handler=server.tool_skill_suggest,
        ),
    }
