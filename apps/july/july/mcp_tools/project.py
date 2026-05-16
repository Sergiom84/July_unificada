from __future__ import annotations

from typing import Any

from july.mcp_utils import ToolSpec, require_string


class ProjectToolHandlers:
    def tool_project_improvement_add(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return self.project_service.add_project_improvement(
            require_string(arguments, "text"),
            repo_path=arguments.get("repo_path"),
            project_key=arguments.get("project_key"),
            priority=arguments.get("priority", "normal"),
            source=arguments.get("source", "mcp"),
        )

    def tool_project_improvements(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return self.project_service.list_project_improvements(
            repo_path=arguments.get("repo_path"),
            project_key=arguments.get("project_key"),
            status=arguments.get("status"),
            include_closed=bool(arguments.get("include_closed", False)),
            limit=int(arguments.get("limit", 20)),
        )

    def tool_project_improvement_status(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return self.project_service.update_project_improvement_status(
            int(arguments["improvement_id"]),
            require_string(arguments, "status"),
            repo_path=arguments.get("repo_path"),
            project_key=arguments.get("project_key"),
        )

    def tool_project_pending_add(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return self.project_service.add_project_pending(
            require_string(arguments, "text"),
            repo_path=arguments.get("repo_path"),
            project_key=arguments.get("project_key"),
            source=arguments.get("source", "mcp"),
        )

    def tool_project_pendings(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return self.project_service.list_project_pendings(
            repo_path=arguments.get("repo_path"),
            project_key=arguments.get("project_key"),
            status=arguments.get("status"),
            include_done=bool(arguments.get("include_done", False)),
            limit=int(arguments.get("limit", 20)),
        )

    def tool_project_pending_status(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return self.project_service.update_project_pending_status(
            int(arguments["pending_id"]),
            require_string(arguments, "status"),
            repo_path=arguments.get("repo_path"),
            project_key=arguments.get("project_key"),
        )

    def tool_project_entry(self, arguments: dict[str, Any]) -> dict[str, Any]:
        limit = int(arguments.get("limit", 5))
        return self.project_service.project_entry(
            repo_path=arguments.get("repo_path"),
            project_key=arguments.get("project_key"),
            limit=limit,
        )

    def tool_project_onboard(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return self.project_service.project_onboard(
            repo_path=arguments.get("repo_path"),
            project_key=arguments.get("project_key"),
            agent_name=arguments.get("agent_name"),
            source=arguments.get("source", "mcp"),
        )

    def tool_project_action(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return self.project_service.project_action(
            require_string(arguments, "action"),
            repo_path=arguments.get("repo_path"),
            project_key=arguments.get("project_key"),
            agent_name=arguments.get("agent_name"),
        )

    def tool_project_ui_link(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return self.cockpit_service.project_ui_link(
            project_key=require_string(arguments, "project_key"),
            repo_path=arguments.get("repo_path"),
        )

    def tool_conversation_checkpoint(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return self.project_service.conversation_checkpoint(
            require_string(arguments, "text"),
            repo_path=arguments.get("repo_path"),
            project_key=arguments.get("project_key"),
            persist=bool(arguments.get("persist", False)),
            source=arguments.get("source", "mcp"),
        )


def build_project_tools(server) -> dict[str, ToolSpec]:
    return {
        "project_improvement_add": ToolSpec(
            name="project_improvement_add",
            title="Add Project Improvement",
            description="Save an idea or possible improvement for the current project so it can be reviewed later.",
            input_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Improvement idea to store."},
                    "repo_path": {"type": "string", "description": "Path to the repository root or any file inside it."},
                    "project_key": {"type": "string", "description": "Optional canonical project key override."},
                    "priority": {"type": "string", "enum": ["low", "normal", "high"]},
                    "source": {"type": "string"},
                },
                "required": ["text"],
            },
            handler=server.tool_project_improvement_add,
        ),
        "project_improvements": ToolSpec(
            name="project_improvements",
            title="Project Improvements",
            description="List open, planned, or all improvement ideas for a project.",
            input_schema={
                "type": "object",
                "properties": {
                    "repo_path": {"type": "string"},
                    "project_key": {"type": "string"},
                    "status": {"type": "string", "enum": ["open", "planned", "in_progress", "done", "dismissed"]},
                    "include_closed": {"type": "boolean"},
                    "limit": {"type": "integer"},
                },
            },
            handler=server.tool_project_improvements,
        ),
        "project_improvement_status": ToolSpec(
            name="project_improvement_status",
            title="Project Improvement Status",
            description="Update an improvement idea status.",
            input_schema={
                "type": "object",
                "properties": {
                    "improvement_id": {"type": "integer"},
                    "status": {"type": "string", "enum": ["open", "planned", "in_progress", "done", "dismissed"]},
                    "repo_path": {"type": "string"},
                    "project_key": {"type": "string"},
                },
                "required": ["improvement_id", "status"],
            },
            handler=server.tool_project_improvement_status,
        ),
        "project_pending_add": ToolSpec(
            name="project_pending_add",
            title="Add Project Pending",
            description="Save a pending or todo item for the current project. It must be marked done when completed.",
            input_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Pending item to store."},
                    "repo_path": {"type": "string", "description": "Path to the repository root or any file inside it."},
                    "project_key": {"type": "string", "description": "Optional canonical project key override."},
                    "source": {"type": "string"},
                },
                "required": ["text"],
            },
            handler=server.tool_project_pending_add,
        ),
        "project_pendings": ToolSpec(
            name="project_pendings",
            title="Project Pendings",
            description="List pending, in-progress, or completed todo items for a project.",
            input_schema={
                "type": "object",
                "properties": {
                    "repo_path": {"type": "string"},
                    "project_key": {"type": "string"},
                    "status": {"type": "string", "enum": ["pending", "in_progress", "done"]},
                    "include_done": {"type": "boolean"},
                    "limit": {"type": "integer"},
                },
            },
            handler=server.tool_project_pendings,
        ),
        "project_pending_status": ToolSpec(
            name="project_pending_status",
            title="Project Pending Status",
            description="Update a pending item status. Use done when the work is completed.",
            input_schema={
                "type": "object",
                "properties": {
                    "pending_id": {"type": "integer"},
                    "status": {"type": "string", "enum": ["pending", "in_progress", "done"]},
                    "repo_path": {"type": "string"},
                    "project_key": {"type": "string"},
                },
                "required": ["pending_id", "status"],
            },
            handler=server.tool_project_pending_status,
        ),
        "project_entry": ToolSpec(
            name="project_entry",
            title="Project Entry",
            description="Return the conversational entry state for a project before onboarding or resuming work.",
            input_schema={
                "type": "object",
                "properties": {
                    "repo_path": {"type": "string", "description": "Path to the repository root or any file inside it."},
                    "project_key": {"type": "string", "description": "Optional canonical project key override."},
                    "limit": {"type": "integer", "description": "Maximum rows per section when reading stored context."},
                },
            },
            handler=server.tool_project_entry,
        ),
        "project_onboard": ToolSpec(
            name="project_onboard",
            title="Project Onboard",
            description="Run the initial read-only onboarding flow and store a first useful snapshot of the repo.",
            input_schema={
                "type": "object",
                "properties": {
                    "repo_path": {"type": "string"},
                    "project_key": {"type": "string"},
                    "agent_name": {"type": "string"},
                    "source": {"type": "string"},
                },
            },
            handler=server.tool_project_onboard,
        ),
        "project_action": ToolSpec(
            name="project_action",
            title="Project Action",
            description="Execute the next conversational project action after the initial wizard prompt.",
            input_schema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["analyze_now", "resume_context", "refresh_context", "continue_without_context", "help", "wait", "do_nothing"],
                    },
                    "repo_path": {"type": "string"},
                    "project_key": {"type": "string"},
                    "agent_name": {"type": "string"},
                },
                "required": ["action"],
            },
            handler=server.tool_project_action,
        ),
        "project_ui_link": ToolSpec(
            name="project_ui_link",
            title="Project UI Link",
            description="Return the deep link URL for the local July Project Cockpit for a project.",
            input_schema={
                "type": "object",
                "properties": {"project_key": {"type": "string"}, "repo_path": {"type": "string"}},
                "required": ["project_key"],
            },
            handler=server.tool_project_ui_link,
        ),
        "conversation_checkpoint": ToolSpec(
            name="conversation_checkpoint",
            title="Conversation Checkpoint",
            description="Classify a conversational finding and optionally persist it as reusable project memory.",
            input_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "repo_path": {"type": "string"},
                    "project_key": {"type": "string"},
                    "persist": {"type": "boolean"},
                    "source": {"type": "string"},
                },
                "required": ["text"],
            },
            handler=server.tool_conversation_checkpoint,
        ),
    }
