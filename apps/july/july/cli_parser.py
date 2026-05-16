from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="july", description="July local-first memory orchestrator MVP")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ── Capture ──────────────────────────────────────────────
    capture = subparsers.add_parser("capture", help="Capture a free-form input into July")
    capture.add_argument("text", nargs="?", help="Raw input to capture. If omitted, stdin is used.")
    capture.add_argument("--source", default="cli", help="Source channel, e.g. cli, telegram, email")
    capture.add_argument("--source-ref", default=None, help="External reference for the source message")
    capture.add_argument("--dry-run", action="store_true", help="Show the classification plan without persisting it")
    capture.add_argument("--use-llm", action="store_true", help="Ask the configured LLM provider to refine the classification")
    capture.add_argument("--fetch-urls", action="store_true", help="Fetch metadata for detected URLs")
    capture.add_argument("--model-name", default=None, help="Name of the model contributing this input (for traceability)")

    # ── Clarify ──────────────────────────────────────────────
    clarify = subparsers.add_parser("clarify", help="Answer a clarification question for an inbox item")
    clarify.add_argument("inbox_item_id", type=int)
    clarify.add_argument("answer", nargs="?", help="Clarification answer. If omitted, stdin is used.")
    clarify.add_argument("--use-llm", action="store_true", help="Ask the configured LLM provider to refine the resolved classification")

    # ── Promote memory ───────────────────────────────────────
    promote = subparsers.add_parser("promote-memory", help="Promote a candidate memory to ready")
    promote.add_argument("memory_item_id", type=int)
    promote.add_argument("--title", default=None)
    promote.add_argument("--summary", default=None)
    promote.add_argument("--knowledge", default=None, help="Override distilled knowledge")
    promote.add_argument("--scope", default=None, choices=["global", "project", "session"])
    promote.add_argument("--importance", type=int, default=None)
    promote.add_argument("--use-llm", action="store_true", help="Ask the configured LLM provider to refine the memory before promoting it")

    # ── List commands ────────────────────────────────────────
    inbox = subparsers.add_parser("inbox", help="List inbox items")
    inbox.add_argument("--limit", type=int, default=20)

    tasks = subparsers.add_parser("tasks", help="List tasks")
    tasks.add_argument("--status", default=None)
    tasks.add_argument("--limit", type=int, default=20)

    memory = subparsers.add_parser("memory", help="List memory items")
    memory.add_argument("--limit", type=int, default=20)

    project_context = subparsers.add_parser("project-context", help="Show inbox/tasks/memory for a project key")
    project_context.add_argument("project_key")
    project_context.add_argument("--limit", type=int, default=10)

    project_entry = subparsers.add_parser("project-entry", help="Return the conversational entry state for a project")
    project_entry.add_argument("--repo-path", default=None, help="Path to the repo to inspect")
    project_entry.add_argument("--project-key", default=None, help="Optional canonical project key override")
    project_entry.add_argument("--limit", type=int, default=5)

    project_onboard = subparsers.add_parser("project-onboard", help="Run the initial read-only onboarding for a project")
    project_onboard.add_argument("--repo-path", default=None, help="Path to the repo to inspect")
    project_onboard.add_argument("--project-key", default=None, help="Optional canonical project key override")
    project_onboard.add_argument("--agent", default=None, help="Agent or model name")
    project_onboard.add_argument("--source", default="cli", help="Source channel for the onboarding trace")

    project_action = subparsers.add_parser("project-action", help="Execute the next conversational action for a project")
    project_action.add_argument(
        "action",
        choices=[
            "analyze_now",
            "resume_context",
            "refresh_context",
            "continue_without_context",
            "help",
            "wait",
            "do_nothing",
        ],
    )
    project_action.add_argument("--repo-path", default=None, help="Path to the repo to inspect")
    project_action.add_argument("--project-key", default=None, help="Optional canonical project key override")
    project_action.add_argument("--agent", default=None, help="Agent or model name")

    checkpoint = subparsers.add_parser("conversation-checkpoint", help="Classify and optionally persist a reusable finding")
    checkpoint.add_argument("text", nargs="?", help="Checkpoint text. If omitted, stdin is used.")
    checkpoint.add_argument("--repo-path", default=None, help="Path to the repo to inspect")
    checkpoint.add_argument("--project-key", default=None, help="Optional canonical project key override")
    checkpoint.add_argument("--persist", action="store_true", help="Persist immediately when the finding is safe or confirmed")
    checkpoint.add_argument("--source", default="cli", help="Source channel for the checkpoint")

    improvement_add = subparsers.add_parser("improvement-add", help="Save a possible project improvement")
    improvement_add.add_argument("text", nargs="?", help="Improvement idea. If omitted, stdin is used.")
    improvement_add.add_argument("--repo-path", default=None, help="Path to the repo to inspect")
    improvement_add.add_argument("--project-key", default=None, help="Optional canonical project key override")
    improvement_add.add_argument("--priority", default="normal", choices=["low", "normal", "high"])
    improvement_add.add_argument("--source", default="cli", help="Source channel for the improvement")

    improvements = subparsers.add_parser("improvements", help="List possible improvements for a project")
    improvements.add_argument("--repo-path", default=None, help="Path to the repo to inspect")
    improvements.add_argument("--project-key", default=None, help="Optional canonical project key override")
    improvements.add_argument("--status", default=None, choices=["open", "planned", "in_progress", "done", "dismissed"])
    improvements.add_argument("--include-closed", action="store_true", help="Include done and dismissed improvements")
    improvements.add_argument("--limit", type=int, default=20)

    improvement_status = subparsers.add_parser("improvement-status", help="Update a project improvement status")
    improvement_status.add_argument("improvement_id", type=int)
    improvement_status.add_argument("status", choices=["open", "planned", "in_progress", "done", "dismissed"])
    improvement_status.add_argument("--repo-path", default=None, help="Path to the repo to inspect")
    improvement_status.add_argument("--project-key", default=None, help="Optional canonical project key override")

    pending_add = subparsers.add_parser("pending-add", help="Save a project pending item")
    pending_add.add_argument("text", nargs="?", help="Pending item. If omitted, stdin is used.")
    pending_add.add_argument("--repo-path", default=None, help="Path to the repo to inspect")
    pending_add.add_argument("--project-key", default=None, help="Optional canonical project key override")
    pending_add.add_argument("--source", default="cli", help="Source channel for the pending item")

    pendings = subparsers.add_parser("pendings", help="List project pending items")
    pendings.add_argument("--repo-path", default=None, help="Path to the repo to inspect")
    pendings.add_argument("--project-key", default=None, help="Optional canonical project key override")
    pendings.add_argument("--status", default=None, choices=["pending", "in_progress", "done"])
    pendings.add_argument("--include-done", action="store_true", help="Include completed pending items")
    pendings.add_argument("--limit", type=int, default=20)

    pending_status = subparsers.add_parser("pending-status", help="Update a project pending item status")
    pending_status.add_argument("pending_id", type=int)
    pending_status.add_argument("status", choices=["pending", "in_progress", "done"])
    pending_status.add_argument("--repo-path", default=None, help="Path to the repo to inspect")
    pending_status.add_argument("--project-key", default=None, help="Optional canonical project key override")

    search = subparsers.add_parser("search", help="Search inbox, tasks, and memory")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=10)

    show = subparsers.add_parser("show", help="Show a single record")
    show.add_argument("table", choices=[
        "inbox_items", "tasks", "memory_items", "artifacts", "project_links",
        "clarification_events", "sessions", "topic_keys", "topic_links",
        "model_contributions", "url_metadata", "external_references", "projects",
        "project_improvements", "skill_references",
    ])
    show.add_argument("record_id", type=int)

    stats = subparsers.add_parser("stats", help="Show database stats")

    export = subparsers.add_parser("export", help="Export the database to JSON")
    export.add_argument("output", nargs="?", default="exports/july-export.json")

    # ── Plug (plugin mode) ──────────────────────────────────
    plug = subparsers.add_parser("plug", help="Plug July into a project: auto-detect, analyze code, and register")
    plug.add_argument("path", nargs="?", default=".", help="Path to the project (default: current directory)")
    plug.add_argument("--project-key", default=None, help="Override the auto-detected project key")
    plug.add_argument("--agent", default=None, help="Agent or model name")
    plug.add_argument("--skip-onboard", action="store_true", help="Skip the initial onboarding step")

    # ── Architect insights ───────────────────────────────────
    architect = subparsers.add_parser("architect", help="Run deep architecture analysis on a project")
    architect.add_argument("path", nargs="?", default=".", help="Path to the project")
    architect.add_argument("--project-key", default=None, help="Project key override")
    architect.add_argument("--json", action="store_true", dest="json_output", help="Output raw JSON")

    subparsers.add_parser("mcp", help="Run the July MCP server over stdio")

    ui = subparsers.add_parser("ui", help="Run the July Project Cockpit on localhost")
    ui.add_argument("--host", default=None, help="Override the UI host")
    ui.add_argument("--port", type=int, default=None, help="Override the UI port")
    ui.add_argument("--open", action="store_true", help="Open the cockpit in the default browser")

    ui_link = subparsers.add_parser("ui-link", help="Build a deep link to the July Project Cockpit")
    ui_link.add_argument("--project-key", required=True, help="Project key to deep-link")
    ui_link.add_argument("--repo-path", default=None, help="Optional repo path to register or refresh")

    # ── Session protocol ─────────────────────────────────────
    ss = subparsers.add_parser("session-start", help="Start a new working session")
    ss.add_argument("session_key", help="Unique key for this session")
    ss.add_argument("--project", default=None, help="Project key for the session")
    ss.add_argument("--agent", default=None, help="Agent or model name")
    ss.add_argument("--goal", default=None, help="Session goal")

    ssm = subparsers.add_parser("session-summary", help="Save a summary for an active session")
    ssm.add_argument("session_key")
    ssm.add_argument("summary", nargs="?", help="Summary text. If omitted, stdin is used.")
    ssm.add_argument("--discoveries", default=None)
    ssm.add_argument("--accomplished", default=None)
    ssm.add_argument("--next-steps", default=None)
    ssm.add_argument("--relevant-files", default=None)

    se = subparsers.add_parser("session-end", help="Close a session")
    se.add_argument("session_key")

    sc = subparsers.add_parser("session-context", help="Recover context from recent sessions")
    sc.add_argument("--project", default=None, help="Filter by project key")
    sc.add_argument("--limit", type=int, default=5)

    sl = subparsers.add_parser("sessions", help="List sessions")
    sl.add_argument("--status", default=None)
    sl.add_argument("--limit", type=int, default=20)

    # ── Topic keys ───────────────────────────────────────────
    tc = subparsers.add_parser("topic-create", help="Create a topic key for grouping related knowledge")
    tc.add_argument("topic_key", help="Stable key like 'auth/jwt-flow' or 'mcp/integration'")
    tc.add_argument("label", help="Human readable label")
    tc.add_argument("--domain", default="Programacion")
    tc.add_argument("--description", default=None)

    tl = subparsers.add_parser("topic-link", help="Link an item to a topic key")
    tl.add_argument("topic_key")
    tl.add_argument("--inbox-item-id", type=int, default=None)
    tl.add_argument("--memory-item-id", type=int, default=None)
    tl.add_argument("--session-id", type=int, default=None)

    tctx = subparsers.add_parser("topic-context", help="Show everything linked to a topic key")
    tctx.add_argument("topic_key")
    tctx.add_argument("--limit", type=int, default=20)

    tls = subparsers.add_parser("topics", help="List all topic keys")
    tls.add_argument("--limit", type=int, default=50)

    # ── Model contributions ──────────────────────────────────
    mc = subparsers.add_parser("model-contribution", help="Record a contribution from an AI model")
    mc.add_argument("model_name", help="Name of the model (claude, codex, zai, gpt, perplexity, genspark...)")
    mc.add_argument("contribution_type", help="Type: proposal, architecture, decision, analysis, suggestion")
    mc.add_argument("title")
    mc.add_argument("content", nargs="?", help="Content text. If omitted, stdin is used.")
    mc.add_argument("--project", default=None)
    mc.add_argument("--domain", default=None)
    mc.add_argument("--adopted", action="store_true")
    mc.add_argument("--notes", default=None)

    mcl = subparsers.add_parser("model-contributions", help="List model contributions")
    mcl.add_argument("--model", default=None)
    mcl.add_argument("--project", default=None)
    mcl.add_argument("--limit", type=int, default=20)

    mca = subparsers.add_parser("adopt-contribution", help="Mark a model contribution as adopted")
    mca.add_argument("contribution_id", type=int)
    mca.add_argument("--notes", default=None)

    # ── URL fetch ────────────────────────────────────────────
    uf = subparsers.add_parser("fetch-url", help="Fetch metadata from a URL and store it")
    uf.add_argument("url")
    uf.add_argument("--artifact-id", type=int, default=None)

    # ── External references ──────────────────────────────────
    ef = subparsers.add_parser("fetch-reference", help="Fetch content from a known reference source")
    ef.add_argument("source_key", choices=["skills.sh", "agents.md"])

    efl = subparsers.add_parser("external-references", help="List stored external references")
    efl.add_argument("--project", default=None)
    efl.add_argument("--limit", type=int, default=20)

    # ── Skill references ─────────────────────────────────────
    sr = subparsers.add_parser("skill-register", help="Register a local skill as a reusable July reference")
    sr.add_argument("path", help="Path to a .skill archive, skill folder, or SKILL.md")
    sr.add_argument("--name", default=None, help="Override the skill name")
    sr.add_argument("--description", default=None, help="Override the skill description")
    sr.add_argument("--trigger", default=None, help="Override trigger/search text")
    sr.add_argument("--domain", action="append", default=[], help="Domain tag used for suggestions; repeatable")
    sr.add_argument("--project-key", action="append", default=[], help="Optional project key to bias suggestions; repeatable")
    sr.add_argument("--status", default="active", choices=["active", "inactive"])

    srl = subparsers.add_parser("skills", help="List registered skill references and local July commands")
    srl.add_argument("--status", default="active", choices=["active", "inactive"])
    srl.add_argument("--include-inactive", action="store_true")
    srl.add_argument("--registered-only", action="store_true", help="Only show reusable skills registered in July")
    srl.add_argument("--limit", type=int, default=20)

    srs = subparsers.add_parser("skill-suggest", help="Suggest registered skills for a text or project context")
    srs.add_argument("text", nargs="?", help="Text to evaluate. If omitted, stdin is used.")
    srs.add_argument("--project-key", default=None)
    srs.add_argument("--limit", type=int, default=5)

    return parser

