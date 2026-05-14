---
name: july
description: Atajo principal para usar July como memoria local de proyecto. Usar cuando Sergio invoque /july, /july con objetivo, quiera recuperar contexto, arrancar o cerrar sesión, guardar memoria operativa, gestionar mejoras/pendientes o guardar punteros seguros.
---

# Skill: /july

`/july` es la puerta principal a July. Su trabajo no es ejecutar código por sí mismo: debe recuperar memoria operativa del proyecto, decidir qué conviene recordar y enrutar a las skills July especializadas cuando aporte claridad.

## Contrato base

- July es memoria operativa: sesiones, contexto de proyecto, hallazgos, errores resueltos, decisiones de iteración, mejoras posibles y pendientes.
- July también puede recordar referencias a skills locales y sugerirlas cuando el objetivo o el contexto encajen.
- `context/wiki/` y `docs/notion/` son conocimiento curado: patrones estables, criterios, análisis y procedimientos reutilizables entre proyectos.
- MCP es la vía preferida. Si las herramientas MCP de July no están disponibles, usa el fallback CLI del repo `C:\Users\sergi\Desktop\Aplicaciones\July_unificada`.
- La experiencia debe ser conversacional. No muestres JSON crudo ni pidas al usuario memorizar comandos internos.
- Usa siempre el proyecto actual (`cwd`) como `repo_path`, salvo que Sergio indique otro.
- En Codex usa `agent_name: "codex"` o `--agent codex`; en Claude Code usa `agent_name: "claude"` o `--agent claude`.

## Enrutado

Cuando Sergio escriba `/july`, `usa july` o una frase equivalente, interpreta los argumentos como una acción sobre el proyecto actual:

| Intención | Acción |
|---|---|
| Sin argumentos, `arranca`, `contexto`, `resume` o `/july <objetivo>` | Ejecuta el flujo de arranque de `/july-inicio`. |
| `wizard`, `onboarding`, `conecta este proyecto` | Ejecuta `/july-wizard`: onboarding read-only, solo con permiso. |
| `guarda <texto>`, `memoria <texto>`, `recuerda <texto>` | Guarda un hallazgo reutilizable del proyecto actual. |
| `secreto <texto>`, `puntero <texto>`, `credencial <texto>` | Guarda solo procedimiento y puntero seguro; nunca el valor secreto. |
| `mejora <texto>` o `idea <texto>` | Guarda una mejora posible del proyecto actual. |
| `mejoras`, `ideas`, `backlog` | Lista mejoras abiertas, planificadas o en progreso. |
| `pendiente <texto>` o `por hacer <texto>` | Guarda un pendiente del proyecto actual. |
| `pendientes`, `qué queda`, `temas abiertos` | Lista pendientes abiertos o en progreso. |
| `ayuda`, `help`, `skills` | Responde como `/july-ayuda`. |
| `comprimir <fichero>` | Ejecuta `/july-comprimir` y aplica sus verificaciones de seguridad. |
| `registrar skill <ruta>` | Registra una skill local como referencia reutilizable si el usuario lo pide explícitamente. |
| `cierra`, `cerrar sesión`, `terminamos` | Resume y cierra la sesión activa si hay información suficiente. |

## Flujo de arranque

Para `/july`, `/july <objetivo>`, `arranca`, `contexto` o `resume`:

1. Detecta el proyecto con `project_entry` usando el `repo_path` actual.
2. Recupera contexto operativo con `project_context`.
3. Recupera sesiones recientes con `session_context` (`limit: 3`).
4. Consulta pendientes con `project_pendings` y mejoras con `project_improvements`.
5. Si Sergio indicó un objetivo, usa `proactive_recall` o `skill_suggest` con ese objetivo y el `project_key`.
6. Revisa `related_context.skill_suggestions` devuelto por `project_entry` y cualquier sugerencia del paso anterior.
7. Abre sesión con `session_start` si el usuario va a trabajar en este proyecto o indicó un objetivo.
8. Resume en español claro:
   - si el proyecto es nuevo, parcial o conocido;
   - qué se sabe de la última sesión;
   - pendientes y mejoras relevantes;
   - skills sugeridas, solo si hay una coincidencia clara;
   - siguiente paso recomendado.
9. Espera instrucción si el siguiente paso requiere elegir entre onboarding, refresh selectivo o tarea concreta.

No hagas onboarding completo solo por invocar `/july`. Si el proyecto es nuevo o el contexto es insuficiente, pregunta antes de usar `project_onboard` o `project_action analyze_now`.

Cuando una skill encaje, dilo como recomendación operativa, por ejemplo: "Oye Sergio, para definir este flujo quizá conviene usar `entrevistador-procesos` antes de construir." No ejecutes la skill sin confirmación si cambiaría el modo de trabajo.

## Qué guardar dónde

| Tipo | Va en | Criterio |
|---|---|---|
| Memoria reutilizable | `conversation_checkpoint --persist` | Error resuelto, decisión de iteración, hallazgo durable o mejora de flujo. |
| Mejora posible | `project_improvement_add` | Idea revisable; no es trabajo decidido todavía. |
| Pendiente | `project_pending_add` | Trabajo decidido o recordatorio operativo por cerrar. |
| Decisión estable o patrón reusable entre proyectos | `context/wiki/` o `docs/notion/` | Criterio curado que Sergio quiere conservar como referencia. |
| Secreto o credencial | Puntero seguro en July, valor fuera de July | Nunca guardar tokens, claves API, valores de `.env` ni credenciales en claro. |

Guarda directamente cuando Sergio lo pida explícitamente y el contenido sea seguro. Pregunta antes de guardar si el dato es ambiguo, sensible, personal, tentativo o demasiado efímero.

## Guardar memoria reutilizable

Para `guarda`, `memoria` o `recuerda`:

1. Identifica el proyecto actual con `project_entry`, `repo_path` o `project_key`.
2. Usa `conversation_checkpoint` con `persist: true` si MCP está disponible.
3. Si MCP no está disponible, usa `conversation-checkpoint --persist`.
4. Si aplica, sugiere o usa un `topic_key` estable como `mcp/integration`, `deploy/render`, `auth/supabase`, `skills/july` o `project/onboarding`.

Responde corto con:

- qué se guardó;
- `memory_item_id` si existe;
- topic o clave detectable;
- qué no se guardó por seguridad.

## Secretos y punteros

Para `secreto`, `puntero` o `credencial`:

- No guardes secretos, claves API, tokens, valores de `.env` ni credenciales en claro.
- Guarda solo servicio, propósito, ubicación segura, nombre de variable si no revela el valor, clave detectable y procedimiento de uso.
- Usa una clave detectable como `<project-key>/<tema>`, por ejemplo `indalo-padel/render-mcp`.
- Si el texto contiene payload sensible, pide al usuario que lo deje en `.env`, Render, Supabase, bóveda local u otro proveedor seguro y guarda solo el puntero.

## Skills relacionadas

| Skill | Uso |
|---|---|
| `/july-inicio` | Arranque normal: detectar proyecto, recuperar contexto, abrir sesión y esperar tarea. |
| `/july-wizard` | Onboarding read-only para un proyecto nuevo o parcial, con permiso explícito. |
| `/july-ayuda` | Chuleta rápida de comandos y reglas de uso. |
| `/july-comprimir` | Compresión segura de ficheros largos de contexto, con validación previa. |
| `/mejoras` | Alias directo si está instalado: listar o gestionar mejoras posibles. |
| `/pendiente` | Alias directo si está instalado: crear o cerrar un pendiente. |
| `/pendientes` | Alias directo si está instalado: listar o actualizar pendientes. |

## Fallback CLI

Desde cualquier repo en Windows:

```powershell
cd C:\Users\sergi\Desktop\Aplicaciones\July_unificada
.\scripts\july.ps1 project-entry --repo-path <repo-actual>
.\scripts\july.ps1 project-context <project-key>
.\scripts\july.ps1 session-context --project <project-key> --limit 3
.\scripts\july.ps1 session-start <session-key> --project <project-key> --agent codex --goal "<objetivo>"
.\scripts\july.ps1 conversation-checkpoint "<memoria reutilizable>" --repo-path <repo-actual> --persist --source codex
.\scripts\july.ps1 improvement-add "<idea>" --repo-path <repo-actual> --source codex
.\scripts\july.ps1 improvements --repo-path <repo-actual>
.\scripts\july.ps1 pending-add "<pendiente>" --repo-path <repo-actual> --source codex
.\scripts\july.ps1 pendings --repo-path <repo-actual>
.\scripts\july.ps1 skill-register "<ruta.skill>" --domain skills --domain procesos
.\scripts\july.ps1 skill-suggest "<objetivo o contexto>" --project-key <project-key>
.\scripts\july.ps1 skills
.\scripts\july.ps1 session-summary <session-key> "<resumen>" --next-steps "<siguiente paso>"
.\scripts\july.ps1 session-end <session-key>
```

Desde cualquier repo en macOS/Linux:

```bash
cd ~/Desktop/Aplicaciones/July_unificada
./apps/july/scripts/july.sh project-entry --repo-path <repo-actual>
./apps/july/scripts/july.sh project-context <project-key>
./apps/july/scripts/july.sh session-context --project <project-key> --limit 3
./apps/july/scripts/july.sh session-start <session-key> --project <project-key> --agent codex --goal "<objetivo>"
./apps/july/scripts/july.sh conversation-checkpoint "<memoria reutilizable>" --repo-path <repo-actual> --persist --source codex
./apps/july/scripts/july.sh improvement-add "<idea>" --repo-path <repo-actual> --source codex
./apps/july/scripts/july.sh improvements --repo-path <repo-actual>
./apps/july/scripts/july.sh pending-add "<pendiente>" --repo-path <repo-actual> --source codex
./apps/july/scripts/july.sh pendings --repo-path <repo-actual>
./apps/july/scripts/july.sh skill-register "<ruta.skill>" --domain skills --domain procesos
./apps/july/scripts/july.sh skill-suggest "<objetivo o contexto>" --project-key <project-key>
./apps/july/scripts/july.sh skills
./apps/july/scripts/july.sh session-summary <session-key> "<resumen>" --next-steps "<siguiente paso>"
./apps/july/scripts/july.sh session-end <session-key>
```

## Reglas

- No modifiques código solo porque se haya invocado `/july`.
- No hagas onboarding completo salvo que el proyecto sea nuevo/parcial y Sergio lo confirme.
- No guardes ruido: una memoria debe ahorrar tiempo, evitar un error futuro o preservar una decisión útil.
- Una mejora posible es una idea revisable; un pendiente es trabajo decidido; una decisión es un criterio adoptado.
- Cuando un pendiente se complete, márcalo como `done`.
- Al cerrar una sesión real, usa `session_summary` y `session_end`.
