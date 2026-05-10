---
name: july-inicio
description: Arranca una sesión de trabajo conectada a July para el proyecto actual. Usar cuando Sergio invoque /july-inicio, /july-inicio <objetivo>, o quiera empezar o retomar un proyecto recuperando contexto reciente desde July.
---

# Skill: /july-inicio

Arranca una sesión de trabajo conectada a July para el proyecto actual.

## Cuándo se usa

Cuando el usuario escribe `/july-inicio` al comenzar a trabajar en cualquier proyecto.

## Lo que debes hacer

Ejecuta estos pasos en orden. No muestres JSON crudo al usuario; sintetiza la respuesta de forma conversacional.

### Paso 1 - Detectar el proyecto

Usa `mcp__july__project_entry` con `repo_path` apuntando al directorio de trabajo actual (`$cwd`). Esto determina si el proyecto es nuevo, parcial o conocido.

### Paso 2 - Abrir sesión

Usa `mcp__july__session_start` con:
- `session_key`: `<project_key>-<YYYY-MM-DD>-<HH:MM>` usando fecha y hora actuales
- `project_key`: el detectado en el paso anterior
- `agent_name`: `Claude` en Claude Code o `Codex` en Codex
- `goal`: el objetivo que el usuario haya indicado al invocar el skill, o vacío si no dijo nada

### Paso 3 - Recuperar contexto reciente

Usa `mcp__july__session_context` con el `project_key` del paso 1, `limit: 3`. Esto trae las últimas sesiones con sus resúmenes, hallazgos y siguientes pasos.

### Paso 4 - Presentar el arranque

Responde de forma conversacional siguiendo este esquema según el estado del proyecto:

**Proyecto conocido:**
> "Este proyecto ya tiene contexto en July. La última sesión fue [fecha] y dejó pendiente: [next_steps]. ¿Continuamos desde ahí o tienes algo nuevo?"

**Proyecto nuevo:**
> "No tengo contexto previo de este proyecto. ¿Quieres que haga un análisis inicial (onboarding) para guardar una primera foto del repo, o prefieres arrancar directamente con una tarea concreta?"

**Si hay pendientes abiertos** (usa `mcp__july__project_pendings` con `project_key`):
> Menciónalos brevemente al final: "Hay [N] pendientes abiertos: [lista corta]."

### Paso 5 - Esperar instrucción

No hagas nada más hasta que el usuario indique qué quiere trabajar.

## Notas

- Si el usuario escribe `/july-inicio <objetivo>`, usa ese texto como `goal` en `session_start`.
- Al cerrar la sesión (cuando el usuario termine), usa `mcp__july__session_summary` + `mcp__july__session_end`.
- Si el proyecto es nuevo y el usuario acepta el onboarding, usa `mcp__july__plug_project`.
- Habla siempre en español con tildes correctas.
