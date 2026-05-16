from __future__ import annotations

from typing import Any

from july.analyzer import analyze_codebase
from july.mcp_utils import ToolSpec
from july.project_conversation import derive_project_key, detect_repo_root


class DeveloperToolHandlers:
    def tool_developer_level(self, arguments: dict[str, Any]) -> dict[str, Any]:
        interaction_type = arguments.get("interaction_type")
        if interaction_type:
            return self.database.record_developer_interaction(
                interaction_type,
                complexity=arguments.get("complexity", "basic"),
                project_key=arguments.get("project_key"),
                detail=arguments.get("detail"),
            )
        profile = self.database.ensure_developer_profile()
        return {
            "level": profile["inferred_level"],
            "profile": profile,
        }

    def tool_architect_insights(self, arguments: dict[str, Any]) -> dict[str, Any]:
        repo_root = detect_repo_root(arguments.get("repo_path"))
        project_key = derive_project_key(repo_root, explicit=arguments.get("project_key"))
        self.database.upsert_project(project_key, str(repo_root), repo_name=repo_root.name)
        analysis = analyze_codebase(repo_root)
        return {
            "project_key": project_key,
            **analysis.to_dict(),
        }

    def tool_plug_project(self, arguments: dict[str, Any]) -> dict[str, Any]:
        repo_root = detect_repo_root(arguments.get("repo_path"))
        project_key = derive_project_key(repo_root, explicit=arguments.get("project_key"))
        self.database.upsert_project(project_key, str(repo_root), repo_name=repo_root.name)

        analysis = analyze_codebase(repo_root)

        onboard_result = None
        if not bool(arguments.get("skip_onboard", False)):
            onboard_result = self.project_service.project_onboard(
                repo_path=str(repo_root),
                project_key=project_key,
                agent_name=arguments.get("agent_name"),
                source="plug",
            )

        entry = self.project_service.project_entry(
            repo_path=str(repo_root),
            project_key=project_key,
        )

        return {
            "project_key": project_key,
            "repo_root": str(repo_root),
            "plugged": True,
            "analysis": analysis.to_dict(),
            "entry": entry,
            "onboard": onboard_result,
        }


def build_developer_tools(server) -> dict[str, ToolSpec]:
    return {
        "architect_insights": ToolSpec(
            name="architect_insights",
            title="Architect Insights",
            description="Run architecture analysis on a project repository and return insights.",
            input_schema={
                "type": "object",
                "properties": {
                    "repo_path": {"type": "string"},
                    "project_key": {"type": "string"},
                },
            },
            handler=server.tool_architect_insights,
        ),
        "developer_level": ToolSpec(
            name="developer_level",
            title="Developer Level",
            description="Get or update the inferred developer level profile.",
            input_schema={
                "type": "object",
                "properties": {
                    "interaction_type": {
                        "type": "string",
                        "enum": ["decision", "architecture_question", "smell_fix", "pattern_apply"],
                    },
                    "complexity": {"type": "string", "enum": ["basic", "intermediate", "advanced"]},
                    "project_key": {"type": "string"},
                    "detail": {"type": "string"},
                },
            },
            handler=server.tool_developer_level,
        ),
        "plug_project": ToolSpec(
            name="plug_project",
            title="Plug Project",
            description="Plug July into a project: auto-detect, analyze code, optionally onboard, and return entry state.",
            input_schema={
                "type": "object",
                "properties": {
                    "repo_path": {"type": "string"},
                    "project_key": {"type": "string"},
                    "agent_name": {"type": "string"},
                    "skip_onboard": {"type": "boolean"},
                },
            },
            handler=server.tool_plug_project,
        ),
    }
