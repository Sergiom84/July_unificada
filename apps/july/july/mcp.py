from __future__ import annotations

import json
import sys
from typing import Any

from july import __version__
from july.cockpit import ProjectCockpitService
from july.config import get_settings
from july.db import JulyDatabase
from july.llm import LLMProviderError, create_llm_provider
from july.mcp_tools import MCPToolHandlers, build_mcp_tools
from july.mcp_utils import ToolSpec
from july.pipeline import apply_classification_overrides
from july.project_conversation import ProjectConversationService

PROTOCOL_VERSION = "2025-03-26"


class JulyMCPServer(MCPToolHandlers):
    def __init__(self) -> None:
        settings = get_settings()
        self.database = JulyDatabase(settings)
        self.llm_provider = create_llm_provider(settings.llm)
        self.project_service = ProjectConversationService(self.database)
        self.cockpit_service = ProjectCockpitService(self.database, settings, self.project_service)
        self.initialized = False
        self.tools = self._build_tools()

    def _build_tools(self) -> dict[str, ToolSpec]:
        return build_mcp_tools(self)

    def serve_stdio(self) -> int:
        for raw_line in sys.stdin:
            line = raw_line.strip()
            if not line:
                continue
            try:
                request = json.loads(line)
            except json.JSONDecodeError:
                self._emit_error(None, -32700, "Parse error")
                continue
            self._handle_message(request)
        return 0

    def _handle_message(self, message: dict[str, Any]) -> None:
        method = message.get("method")
        message_id = message.get("id")
        params = message.get("params") or {}

        if method == "initialize":
            self._emit_result(
                message_id,
                {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": "July", "version": __version__},
                    "instructions": (
                        "July is a local-first memory orchestrator with architect copilot capabilities. "
                        "It exposes memory capture, search, sessions, topic keys, "
                        "model traceability, URL fetching, proactive recall, "
                        "project conversation layer for wizard-like onboarding, "
                        "deep links to the local project cockpit UI, "
                        "deep code analysis (architect_insights, plug_project), "
                        "and developer level inference (developer_level). "
                        "Use plug_project to connect July to a new project with full analysis. "
                        "Use architect_insights for on-demand architecture review. "
                        "Use developer_level to track and adapt to the developer's skill level."
                    ),
                },
            )
            return

        if method == "notifications/initialized":
            self.initialized = True
            return

        if method == "ping":
            self._emit_result(message_id, {})
            return

        if method == "tools/list":
            self._emit_result(
                message_id,
                {
                    "tools": [
                        {
                            "name": tool.name,
                            "title": tool.title,
                            "description": tool.description,
                            "inputSchema": tool.input_schema,
                        }
                        for tool in self.tools.values()
                    ]
                },
            )
            return

        if method == "tools/call":
            self._handle_tool_call(message_id, params)
            return

        self._emit_error(message_id, -32601, f"Method not found: {method}")

    def _handle_tool_call(self, message_id: Any, params: dict[str, Any]) -> None:
        tool_name = params.get("name")
        arguments = params.get("arguments") or {}
        tool = self.tools.get(tool_name)
        if tool is None:
            self._emit_error(message_id, -32602, f"Unknown tool: {tool_name}")
            return

        try:
            result = tool.handler(arguments)
            self._emit_result(
                message_id,
                {
                    "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=True)}],
                    "structuredContent": result,
                },
            )
        except (ValueError, LLMProviderError) as exc:
            self._emit_result(
                message_id,
                {
                    "content": [{"type": "text", "text": str(exc)}],
                    "isError": True,
                },
            )
        except Exception as exc:  # pragma: no cover
            self._emit_result(
                message_id,
                {
                    "content": [{"type": "text", "text": f"Unexpected server error: {exc}"}],
                    "isError": True,
                },
            )

    def _emit_result(self, message_id: Any, result: dict[str, Any]) -> None:
        response = {"jsonrpc": "2.0", "id": message_id, "result": result}
        sys.stdout.write(json.dumps(response, ensure_ascii=True) + "\n")
        sys.stdout.flush()

    def _emit_error(self, message_id: Any, code: int, message: str) -> None:
        response = {"jsonrpc": "2.0", "id": message_id, "error": {"code": code, "message": message}}
        sys.stdout.write(json.dumps(response, ensure_ascii=True) + "\n")
        sys.stdout.flush()

    def _maybe_enrich_capture_with_llm(
        self,
        raw_input: str,
        plan: dict[str, Any],
        clarification_answer: str | None = None,
    ) -> dict[str, Any]:
        overrides = self.llm_provider.enrich_capture(raw_input, plan)
        if not overrides:
            return plan
        return apply_classification_overrides(raw_input, plan, overrides, clarification_answer=clarification_answer)

    def _maybe_draft_memory_with_llm(self, memory_item) -> dict[str, Any]:
        inbox_item_id = memory_item["inbox_item_id"]
        raw_input = ""
        if inbox_item_id:
            inbox_item = self.database.get_record("inbox_items", inbox_item_id)
            if inbox_item is not None:
                raw_input = inbox_item["raw_input"]
        return self.llm_provider.draft_memory(raw_input, dict(memory_item)) or {}


def main() -> int:
    server = JulyMCPServer()
    return server.serve_stdio()
