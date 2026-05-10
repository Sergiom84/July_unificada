# Project Instructions

## Purpose

This repository is the unified local memory and copilot workspace for Sergio.

It combines a curated procedural knowledge base with the July local-first memory engine.

Codex should help maintain this repository as a persistent wiki and operational memory workspace so Sergio does not have to repeat context across sessions.

Keep the two layers conceptually separate:

- `context/` and `docs/` are curated knowledge.
- `apps/july/` is executable software.

## Directory Structure

- `apps/july/`: July application code, CLI, MCP server, cockpit, tests, and its own project documentation.
- `context/raw/`: original source material. Treat as immutable.
- `context/raw/assets/`: images, exports, attachments, PDFs, screenshots, and related files.
- `context/wiki/index.md`: main map of the generated wiki.
- `context/wiki/log.md`: chronological log of ingests, queries, decisions, and maintenance.
- `context/wiki/sources/`: one page per source document.
- `context/wiki/entities/`: people, companies, products, tools, apps, clients, projects.
- `context/wiki/concepts/`: reusable ideas, patterns, procedures, methods, and risks.
- `context/wiki/decisions/`: decisions Sergio wants to preserve.
- `context/wiki/analyses/`: synthesized investigations, comparisons, and reports.
- `docs/notion/`: curated procedure documents intended for Notion or stable reference.
- `scripts/`: root-level helper scripts and wrappers.
- `skills/`: local skills or skill notes that belong to this unified workspace.

## Shared Local Skills

Use `skills/` as the source of truth for Sergio's custom local skills across machines.

Claude Code should load these through `~/.claude/skills` or `%USERPROFILE%\.claude\skills`, preferably as a symlink to this repository's `skills/` directory.

Codex does not rely on Claude's `~/.claude/skills` autocompletion. When Sergio refers to one of these commands, treat the matching local skill in `skills/` as the procedure to follow:

Keep repo-owned July wrappers with the explicit `july-` prefix so their origin is obvious and Claude Code can autocomplete them. Do not rename them to generic commands like `/inicio` or `/comprimir`. Third-party or global skills keep their native names, for example `/caveman-compress`.

| Command | Source | Purpose |
|---|---|---|
| `/july` | `skills/july/SKILL.md` | Short alias to start a July-backed project session and recover context. |
| `/july-inicio` | `skills/july-inicio/SKILL.md` | Start a July-backed project session and recover recent context. |
| `/july-wizard` | `skills/july-wizard/SKILL.md` | Run read-only onboarding for a new or partial project in July. |
| `/july-comprimir` | `skills/july-comprimir/SKILL.md` | Compress a long procedural/context file with Caveman safeguards. |
| `/july-ayuda` | `skills/july-ayuda/SKILL.md` | Show the quick help sheet for July, Caveman, and common agent commands. |

## Core Rules

1. Treat `context/raw/` as read-only unless Sergio explicitly asks to edit it.
2. Treat `context/wiki/` as Codex-maintained.
3. Before answering procedural or project-memory questions, check July first (`project_context`, `session_context`), then consult `context/wiki/index.md` if July no tiene respuesta.
4. When ingesting a new source, create wiki pages **only** if the content has cross-project, stable, reusable value (patterns, procedures, entities, concepts). Session-specific or project-specific discoveries go to July, not to the wiki.
5. Use Obsidian-style wikilinks: `[[Page Name]]`.
6. Flag contradictions clearly instead of silently choosing one claim.
7. Cite source files whenever possible.
8. Update `context/wiki/index.md` after every meaningful wiki change.
9. Append an entry to `context/wiki/log.md` after every ingest, query, lint pass, or major update.
10. Prefer small, precise edits over rewriting large pages unnecessarily.
11. When working inside `apps/july/`, also follow `apps/july/AGENTS.md`, `apps/july/README.md`, `apps/july/ROADMAP.md`, and `apps/july/PROJECT_PROTOCOL.md` when present.
12. Do not store July's live database inside this repo. It belongs in `~/.july/july.db` (macOS/Linux) o `C:\Users\sergi\.july\july.db` (Windows).

## Regla de separación de memoria

**July** es la memoria operativa. Va aquí:
- Estado de sesión y contexto de proyecto
- Hallazgos, errores resueltos y decisiones tomadas durante una iteración
- Mejoras posibles (`project_improvement_add`) y pendientes (`project_pending_add`)
- Todo lo que un agente necesita recuperar al volver a un proyecto

**`context/wiki/`** es el conocimiento curado y estable. Va aquí:
- Patrones reutilizables entre proyectos (web de cliente, SEO, formularios, etc.)
- Entidades duraderas: personas, empresas, herramientas
- Análisis y síntesis que Sergio quiere conservar como referencia
- Procedimientos y checklists en `docs/notion/`

**Regla práctica:** July recuerda la sesión. La wiki conserva el criterio.

## Page Conventions

Every generated wiki page should start with YAML frontmatter:

```yaml
---
type: source | entity | concept | decision | analysis | index | log
status: draft | active | needs-review | superseded
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources:
  - context/raw/source-file.ext
tags:
  - example
---
```

Use lowercase kebab-case filenames:

- `context/wiki/concepts/wiki-persistente-para-codex.md`
- `context/wiki/decisions/usar-wiki-local-en-este-proyecto.md`

Use clear Spanish page titles as the first heading.

## Ingest Workflow

When Sergio asks to ingest a source:

1. Read the source from `context/raw/` or the explicit path provided.
2. Create or update a source page in `context/wiki/sources/`.
3. Extract important entities and update or create pages in `context/wiki/entities/`.
4. Extract important concepts and update or create pages in `context/wiki/concepts/`.
5. Identify decisions, recommendations, contradictions, open questions, and reusable insights.
6. Create or update decision pages in `context/wiki/decisions/` when useful.
7. Update `context/wiki/index.md`.
8. Append a dated entry to `context/wiki/log.md`.

## Query Workflow

When Sergio asks a question that may depend on memory:

1. Read `context/wiki/index.md`.
2. Identify relevant pages.
3. Read those pages before answering.
4. If the answer produces reusable knowledge, propose where to save it.
5. If Sergio asks to save it, update the wiki and log.

## Maintenance Workflow

When Sergio asks to lint or maintain the wiki, check for:

- orphan pages
- broken wikilinks
- duplicated concepts
- stale claims
- contradictions
- source pages not reflected in entity, concept, decision, or analysis pages
- important concepts without their own page
- pages missing YAML frontmatter

Produce a maintenance report first. Apply fixes only when requested.

## Style

- Write in Spanish unless Sergio asks otherwise.
- Use correct Spanish spelling, including accents, `ñ`, opening question marks, and opening exclamation marks. Do not strip accents for ASCII unless editing code identifiers, commands, paths, or machine-readable values.
- Keep procedure documents concise, practical, and reusable.
- Prefer checklists for repeatable operations.
- Prefer tables for comparisons.
- Do not invent source claims.
- Mark uncertainty explicitly.
- Keep raw source material separate from distilled wiki knowledge.

## Working With This Repository

This repository may not have code, tests, or Git history. Do not assume normal software-project commands exist.

When making changes:

1. Inspect the relevant wiki or docs files first.
2. Edit only the necessary files.
3. Keep `docs/notion/` for polished procedures.
4. Keep `context/wiki/` for active memory and evolving knowledge.
5. Summarize changed files clearly.
