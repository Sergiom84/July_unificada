from __future__ import annotations

from july.mcp_utils import ToolSpec
from july.mcp_tools.developer import DeveloperToolHandlers, build_developer_tools
from july.mcp_tools.memory import MemoryToolHandlers, build_memory_tools
from july.mcp_tools.project import ProjectToolHandlers, build_project_tools
from july.mcp_tools.references_skills import ReferenceSkillToolHandlers, build_reference_skill_tools
from july.mcp_tools.sessions_topics import SessionTopicToolHandlers, build_session_topic_tools


class MCPToolHandlers(
    MemoryToolHandlers,
    ProjectToolHandlers,
    SessionTopicToolHandlers,
    ReferenceSkillToolHandlers,
    DeveloperToolHandlers,
):
    pass


def build_mcp_tools(server) -> dict[str, ToolSpec]:
    tools: dict[str, ToolSpec] = {}
    for family in (
        build_memory_tools,
        build_project_tools,
        build_session_topic_tools,
        build_reference_skill_tools,
        build_developer_tools,
    ):
        tools.update(family(server))
    return tools
