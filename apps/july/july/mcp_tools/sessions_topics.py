from __future__ import annotations

from typing import Any

from july.mcp_utils import ToolSpec, require_string


class SessionTopicToolHandlers:
    def tool_session_start(self, arguments: dict[str, Any]) -> dict[str, Any]:
        session_key = require_string(arguments, "session_key")
        return self.database.session_start(
            session_key,
            project_key=arguments.get("project_key"),
            agent_name=arguments.get("agent_name"),
            goal=arguments.get("goal"),
        )

    def tool_session_summary(self, arguments: dict[str, Any]) -> dict[str, Any]:
        session_key = require_string(arguments, "session_key")
        summary = require_string(arguments, "summary")
        return self.database.session_summary(
            session_key,
            summary=summary,
            discoveries=arguments.get("discoveries"),
            accomplished=arguments.get("accomplished"),
            next_steps=arguments.get("next_steps"),
            relevant_files=arguments.get("relevant_files"),
        )

    def tool_session_end(self, arguments: dict[str, Any]) -> dict[str, Any]:
        session_key = require_string(arguments, "session_key")
        return self.database.session_end(session_key)

    def tool_session_context(self, arguments: dict[str, Any]) -> dict[str, Any]:
        project_key = arguments.get("project_key")
        limit = int(arguments.get("limit", 5))
        return {"sessions": self.database.session_context(project_key=project_key, limit=limit)}

    def tool_topic_create(self, arguments: dict[str, Any]) -> dict[str, Any]:
        topic_key = require_string(arguments, "topic_key")
        label = require_string(arguments, "label")
        domain = arguments.get("domain", "Programacion")
        description = arguments.get("description")
        return self.database.create_topic(topic_key, label, domain, description=description)

    def tool_topic_link(self, arguments: dict[str, Any]) -> dict[str, Any]:
        topic_key = require_string(arguments, "topic_key")
        return self.database.link_to_topic(
            topic_key,
            inbox_item_id=arguments.get("inbox_item_id"),
            memory_item_id=arguments.get("memory_item_id"),
            session_id=arguments.get("session_id"),
        )

    def tool_topic_context(self, arguments: dict[str, Any]) -> dict[str, Any]:
        topic_key = require_string(arguments, "topic_key")
        limit = int(arguments.get("limit", 20))
        return self.database.topic_context(topic_key, limit=limit)


def build_session_topic_tools(server) -> dict[str, ToolSpec]:
    return {
        "session_start": ToolSpec(
            name="session_start",
            title="Session Start",
            description="Start a new working session. Returns session id and status.",
            input_schema={
                "type": "object",
                "properties": {
                    "session_key": {"type": "string", "description": "Unique session key."},
                    "project_key": {"type": "string"},
                    "agent_name": {"type": "string"},
                    "goal": {"type": "string"},
                },
                "required": ["session_key"],
            },
            handler=server.tool_session_start,
        ),
        "session_summary": ToolSpec(
            name="session_summary",
            title="Session Summary",
            description="Save a structured summary for the current session before closing it.",
            input_schema={
                "type": "object",
                "properties": {
                    "session_key": {"type": "string"},
                    "summary": {"type": "string"},
                    "discoveries": {"type": "string"},
                    "accomplished": {"type": "string"},
                    "next_steps": {"type": "string"},
                    "relevant_files": {"type": "string"},
                },
                "required": ["session_key", "summary"],
            },
            handler=server.tool_session_summary,
        ),
        "session_end": ToolSpec(
            name="session_end",
            title="Session End",
            description="Close a session. If no summary was saved, it will be marked as closed_without_summary.",
            input_schema={
                "type": "object",
                "properties": {"session_key": {"type": "string"}},
                "required": ["session_key"],
            },
            handler=server.tool_session_end,
        ),
        "session_context": ToolSpec(
            name="session_context",
            title="Session Context",
            description="Recover context from recent sessions, optionally filtered by project.",
            input_schema={
                "type": "object",
                "properties": {"project_key": {"type": "string"}, "limit": {"type": "integer"}},
            },
            handler=server.tool_session_context,
        ),
        "topic_create": ToolSpec(
            name="topic_create",
            title="Create Topic",
            description="Create a stable topic key for grouping related knowledge across sessions and projects.",
            input_schema={
                "type": "object",
                "properties": {
                    "topic_key": {"type": "string", "description": "Stable key like 'auth/jwt-flow' or 'mcp/integration'."},
                    "label": {"type": "string"},
                    "domain": {"type": "string"},
                    "description": {"type": "string"},
                },
                "required": ["topic_key", "label"],
            },
            handler=server.tool_topic_create,
        ),
        "topic_link": ToolSpec(
            name="topic_link",
            title="Link to Topic",
            description="Link an inbox item, memory item, or session to a topic key.",
            input_schema={
                "type": "object",
                "properties": {
                    "topic_key": {"type": "string"},
                    "inbox_item_id": {"type": "integer"},
                    "memory_item_id": {"type": "integer"},
                    "session_id": {"type": "integer"},
                },
                "required": ["topic_key"],
            },
            handler=server.tool_topic_link,
        ),
        "topic_context": ToolSpec(
            name="topic_context",
            title="Topic Context",
            description="Show everything linked to a topic key: memories, sessions, inbox items.",
            input_schema={
                "type": "object",
                "properties": {"topic_key": {"type": "string"}, "limit": {"type": "integer"}},
                "required": ["topic_key"],
            },
            handler=server.tool_topic_context,
        ),
    }
