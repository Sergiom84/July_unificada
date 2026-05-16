---
name: visual-copilot
description: |
  Create evidence-based interactive HTML maps from real projects, codebases, generated architectures, or complex AI outputs. Use when the user asks to understand how a project is connected, where each section/module/component lives, where flow breaks, which nodes are well anchored or weak, or says: "visual-copilot", "mapa", "visual", "show the map", "show me the flow", "map this project", "map this module", "show dependencies", "concept map", "muéstrame el flujo", "dónde se rompe el flujo", "qué está conectado", "qué nodo está flojo". Compatible with Codex, Claude Code, Claude, ChatGPT-style agents, and local coding agents. For code projects, always read real files first and never invent nodes or relationships.
---

# Visual Copilot

Create a self-contained interactive HTML file that explains how a project, module, workflow, or structured document is connected.

Primary goal: help Sergio and the agent see where each part is located, what it connects to, which nodes are well anchored, which are weak or broken, and where the flow may be failing.

The output must be useful for debugging architecture and navigation, not just visually attractive.

## Agent Compatibility

Use agent-neutral behavior:

- In Codex, use available shell/search/edit/browser tools.
- In Claude Code, use Read/Grep/Glob/Bash/Edit or equivalent tools.
- In other local agents, use the closest available file-reading and HTML-writing tools.
- Never rely on a model-specific feature when a plain file read, static search, and single HTML output can do the job.
- Support Windows, macOS, and Linux paths. Preserve exact file paths from the project.

## Modes

### Mode 1: Project Flow Map

Use for existing codebases or generated multi-file projects.

This is the main mode.

Output: an interactive HTML map showing real nodes, real relationships, evidence, stability status, possible breaks, and investigation notes.

### Mode 2: Document Dashboard

Use for complex non-code outputs: plans, analyses, reports, roadmaps, risk registers, and structured responses.

Output: a dark-theme HTML dashboard with tabs, KPI cards, SVG diagrams, timelines, and tables.

Do not automatically create a dashboard for every long response. Offer it when useful; create it when the user asks.

## Project Flow Workflow

### 1. Define scope

Infer the smallest useful scope from the user request:

- Full project
- App area
- Screen/page
- Module/package
- Feature flow
- API/data flow
- Recently generated architecture

If the scope is unclear but the user wants a project-wide map, analyze the whole project while excluding generated/vendor/build folders.

Default output path:

- Use `docs/visual-copilot.html` when `docs/` exists.
- Otherwise use `visual-copilot.html` in the project root.
- If the user names a path, use that path.

### 2. Inventory the project

Read the real project before generating the map.

Start with:

- File tree: `rg --files` or equivalent.
- Project manifests: `package.json`, `pnpm-workspace.yaml`, `turbo.json`, `vite.config.*`, `next.config.*`, `tsconfig.json`, `pyproject.toml`, `requirements.txt`, `Cargo.toml`, `go.mod`, `composer.json`, or equivalents.
- App entry points, routers, pages/screens, layouts, controllers, API routes, stores/context/state, data models/schemas, service/API clients, shared utilities, tests, and config.

Ignore by default:

- `.git/`
- `node_modules/`
- `.next/`, `dist/`, `build/`, `out/`
- `coverage/`
- cache/temp folders
- lockfiles unless dependency context is needed
- generated assets unless they define routes or contracts

### 3. Extract graph data

Build the graph from evidence. Prefer static facts over guesses.

Use this internal schema:

```yaml
nodes:
  - id: stable-kebab-id
    label: Human readable name
    type: app | route | screen | section | component | api | model | store | util | config | test | external
    file: exact/project/path.ext
    lines: "12-48"
    description: One-line description based on code or comments
    stability: fixed | weak | broken | unknown
    reason: Why the stability status was assigned
    evidence:
      - "file:line - observed fact"
    critical: true | false

edges:
  - from: node-id
    to: node-id
    kind: navigation | composition | data-flow | mutation | dependency | config | test | external | candidate
    label: specific relationship phrase
    status: confirmed | weak | broken | unconfirmed
    evidence:
      - "file:line - import/call/route/selector/schema/etc."
    reason: Why this relationship matters or may be failing
    critical: true | false
```

Do not expose raw YAML unless useful. Use it internally to build the HTML.

### 4. Classify node stability

Use these meanings consistently:

- `fixed`: The node is clearly anchored by real evidence such as a route, entry point, import chain, API contract, store usage, schema, or test. It has coherent incoming/outgoing relationships for its role.
- `weak`: The node exists but appears fragile: orphaned, duplicated, dynamically referenced, missing tests, has unclear ownership, has only one-sided connections, or depends on implicit conventions.
- `broken`: Evidence indicates a real break: missing import target, dead route, undefined endpoint, mismatched model/schema, incompatible prop/data shape, unreachable screen, failing test reference, or a referenced file/function that does not exist.
- `unknown`: The agent could not read enough context to classify safely.

Never mark a node as `fixed` just because it exists.

### 5. Classify edge status

Use these meanings consistently:

- `confirmed`: Direct evidence proves the relationship.
- `weak`: Evidence exists but is fragile, indirect, dynamic, convention-based, or missing a complementary connection.
- `broken`: A relationship is attempted but appears invalid or incomplete.
- `unconfirmed`: There is a concrete hint, but the agent cannot prove the target or behavior from available files.

Never create an edge without at least one evidence item. If there is no evidence, omit the edge and mention the gap in the findings panel.

### 6. Detect flow issues

Include a findings panel in the HTML with:

- Broken nodes and broken edges
- Weak nodes that may explain the failed flow
- Orphaned nodes or unreachable screens
- Missing route targets
- API calls without matching client/server contract
- Store/model shape mismatches
- Duplicate sources of truth
- Dynamic imports/routes that need manual confirmation
- Tests that cover or fail to cover critical flow
- Files that could not be read

Each finding must include file evidence when possible.

## Rendering Requirements

Generate one complete HTML file from `<!DOCTYPE html>` to `</html>`.

No external dependencies:

- Inline CSS
- Inline JavaScript
- Inline SVG
- No CDN
- No external fonts

Use a dark, high-contrast interface:

- Background: `#0f1117`
- Surface: `#151924`
- Text: `#e2e8f0`
- Muted text: `#94a3b8`
- Accent: `#6366f1`
- Danger: `#ef4444`
- Warning: `#f59e0b`
- Success: `#22c55e`

Do not use a decorative landing page. The first screen is the actual map/tool.

### Required HTML UI

Include:

- Header with project name, scope, generation date, and analyzed root.
- Summary KPIs: total nodes, total edges, fixed nodes, weak nodes, broken nodes, unknown nodes.
- Interactive graph view.
- Findings panel sorted by severity.
- Node detail panel.
- Relationship detail panel.
- Search box for node/file names.
- Filters for node type, stability, and edge status.
- Toggle: `Mostrar todo / Solo críticos`.
- Toggle: `Mostrar evidencia`.
- Legend for node types, stability states, and edge styles.
- Table view with all nodes and edges.
- File coverage section listing analyzed files and skipped/unread files.

### Graph layout

Use a deterministic layout:

- Put the central app/module/scope node in the center.
- Put first-level critical nodes around it.
- Put second-level nodes further out.
- For large graphs, group by type or folder and keep the initial view readable.
- Minimum working canvas: 1200 x 800.
- Support pan and zoom with buttons or mouse controls when practical.

Prefer radial or layered layout. Use force-directed layout only if implemented inline and tested.

### Node visual language

Node type colors:

| Type | Color |
|---|---|
| app | `#6366f1` |
| route/screen/section | `#3b82f6` |
| component | `#06b6d4` |
| api | `#f59e0b` |
| model | `#22c55e` |
| store | `#a855f7` |
| util/config | `#6b7280` |
| test | `#84cc16` |
| external | `#ef4444` |

Stability overlays:

- `fixed`: solid border
- `weak`: amber border
- `broken`: red border plus warning marker
- `unknown`: dashed border

### Edge visual language

- Navigation/composition: solid line with arrow
- Data flow/mutation: dashed line with arrow
- Dependency/config/test: dotted line
- Broken: red line
- Weak/unconfirmed: amber line

Edge labels must be specific:

- Good: `renderiza PlayersTable`, `lee sessionStore.user`, `POST /api/players`, `navega a /players/:id`
- Bad: `uses`, `calls`, `connects`

## Evidence Rules

Every node and edge must be traceable.

Evidence format:

```text
path/to/file.ext:line - what was observed
```

If exact line numbers are unavailable, use:

```text
path/to/file.ext - what was observed
```

Never invent:

- Files
- Routes
- Components
- APIs
- Stores
- Functions
- Relationships
- Tests

If the agent suspects a relationship but cannot prove it, include it only as `status: unconfirmed` with the concrete hint that caused the suspicion.

## Document Dashboard Rules

For non-code structured content, generate a self-contained HTML dashboard with:

- Tabs by section
- KPI cards
- Flow diagrams
- Timelines
- Risk/decision tables
- Search or quick navigation when useful

Use this mode only when the source is a document/output rather than a code project.

## Validation

Before final response:

1. Confirm the HTML file exists at the chosen path.
2. Confirm it starts with `<!DOCTYPE html>` and ends with `</html>`.
3. Check that CSS and JS are inline.
4. Check that there are no external CDN/script/font dependencies.
5. Check that every graph node has at least one evidence item unless it represents the top-level analyzed scope.
6. Check that every edge has at least one evidence item.
7. If a browser tool is available, open the HTML and verify the graph renders, filters work, and no obvious console/runtime error appears.

If validation cannot be fully performed, state exactly what was and was not verified.

## Final Response

Respond in the user's language.

Include:

- HTML file path
- Scope analyzed
- Most important broken/weak flow findings
- Validation performed
- Any important unread files or uncertainty

Keep the final answer concise. Do not paste the full HTML unless the user explicitly asks.

## Proactive Offer

After generating or modifying a multi-file architecture, offer a map only when it would help the user understand the structure:

`¿Quieres que genere el mapa visual del flujo real del proyecto para ver nodos, relaciones y posibles roturas?`
