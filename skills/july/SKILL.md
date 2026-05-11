---
name: july
description: Atajo corto para usar July como memoria local de proyecto. Usar cuando Sergio invoque /july, /july con objetivo, quiera arrancar sesión, recuperar contexto, ver pendientes, guardar conocimiento operativo, guardar memoria de proyecto o guardar punteros seguros a secretos.
---

# Skill: /july

Atajo corto para trabajar con July desde cualquier proyecto.

## Enrutado

Cuando Sergio escriba `/july`, `usa july` o una frase equivalente, interpreta los argumentos como acción sobre el proyecto actual:

- Sin argumentos, `arranca`, `contexto`, `resume` o `/july <objetivo>`: sigue el mismo procedimiento de `skills/july-inicio/SKILL.md`.
- `guarda <texto>`, `memoria <texto>`, `recuerda <texto>`: guarda un hallazgo reutilizable del proyecto actual.
- `secreto <texto>`, `puntero <texto>`, `credencial <texto>`: guarda solo el procedimiento y el puntero seguro, nunca el valor secreto.
- `mejora <texto>` o `idea <texto>`: guarda una posible mejora del proyecto actual.
- `mejoras`, `ideas`, `backlog`: lista mejoras abiertas, planificadas o en progreso.
- `pendiente <texto>` o `por hacer <texto>`: guarda un pendiente del proyecto actual.
- `pendientes`: lista pendientes abiertos o en progreso.
- `ayuda`, `help`, `skills`: responde como `/july-ayuda`.
- `comprimir`: aplica `/july-comprimir`.
- `cierra`: resume la sesión y cierra el ciclo en July si hay información suficiente.

## Arrancar o Recuperar Contexto

Para `/july`, `/july <objetivo>`, `arranca`, `contexto` o `resume`:

1. Detecta el proyecto actual con `mcp__july__project_entry`.
2. Abre sesión con `mcp__july__session_start`.
3. Recupera contexto reciente con `mcp__july__session_context`.
4. Consulta pendientes abiertos con `mcp__july__project_pendings`.
5. Resume el estado en español claro y espera la siguiente instrucción.

Usa `agent_name: "Claude"` en Claude Code o `agent_name: "Codex"` en Codex.

## Guardar Memoria Reutilizable

Para `guarda`, `memoria` o `recuerda`:

1. Identifica el proyecto actual (`repo_path` o `project_key`).
2. Guarda con MCP `conversation_checkpoint` usando `persist: true` si está disponible.
3. Si MCP no está disponible, usa el fallback CLI `conversation-checkpoint --persist`.
4. Si aplica, enlaza o sugiere un topic estable como `mcp/integration`, `deploy/render` o `auth/supabase`.

Responde corto con:
- qué se guardó
- `memory_item_id` si existe
- topic o clave detectable
- qué no se guardó por seguridad

## Secretos y Punteros

Para `secreto`, `puntero` o `credencial`:

- No guardes secretos, claves API, tokens, valores de `.env` ni credenciales en claro.
- Guarda solo: servicio, propósito, ubicación segura (`.env`, Render, Supabase, bóveda), nombre de variable si no revela el valor, clave detectable y procedimiento de uso.
- Usa una clave detectable como `<project-key>/<tema>`, por ejemplo `indalo-padel/render-mcp`.
- Si hay payload sensible, guárdalo en la bóveda segura o deja puntero al `.env`/proveedor.
- Pregunta antes de guardar información ambigua, personal o sensible.

Ejemplo:

```text
/july guarda esto para este proyecto:
Para acceder a Render mediante MCP, usar el service ID srv-xxx. El token no debe guardarse en claro; está en .env como MCP_RENDER_SECOND_WS. Topic recomendado: mcp/integration. Clave detectable futura: indalo-padel/render-mcp.
```

## Fallback CLI

Desde cualquier repo en Windows:

```powershell
cd C:\Users\sergi\Desktop\Aplicaciones\July_unificada
.\scripts\july.ps1 project-entry --repo-path <repo-actual>
.\scripts\july.ps1 conversation-checkpoint "<memoria reutilizable>" --repo-path <repo-actual> --persist --source codex
.\scripts\july.ps1 improvement-add "<idea>" --repo-path <repo-actual>
.\scripts\july.ps1 improvements --repo-path <repo-actual>
.\scripts\july.ps1 pending-add "<pendiente>" --repo-path <repo-actual>
.\scripts\july.ps1 pendings --repo-path <repo-actual>
```

Desde cualquier repo en Mac:

```bash
cd ~/Desktop/Aplicaciones/July_unificada
./apps/july/scripts/july.sh project-entry --repo-path <repo-actual>
./apps/july/scripts/july.sh conversation-checkpoint "<memoria reutilizable>" --repo-path <repo-actual> --persist --source codex
./apps/july/scripts/july.sh improvement-add "<idea>" --repo-path <repo-actual>
./apps/july/scripts/july.sh improvements --repo-path <repo-actual>
./apps/july/scripts/july.sh pending-add "<pendiente>" --repo-path <repo-actual>
./apps/july/scripts/july.sh pendings --repo-path <repo-actual>
```

## Reglas

- No modifiques código solo porque se haya invocado `/july`.
- No hagas onboarding completo salvo que el proyecto sea nuevo y Sergio lo confirme.
- Una memoria es conocimiento reutilizable; una mejora posible es una idea; una tarea es trabajo decidido; una decisión es un criterio adoptado.
- Un pendiente es trabajo por hacer y debe marcarse como `done` al completarse.
- Al cerrar una sesión, usa `mcp__july__session_summary` y `mcp__july__session_end`.
