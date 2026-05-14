---
name: july-inicio
description: Arranca una sesión de trabajo conectada a July para el proyecto actual. Usar cuando Sergio invoque /july-inicio, /july-inicio <objetivo>, o quiera empezar o retomar un proyecto recuperando contexto reciente desde July.
---

# Skill: /july-inicio

Arranca una sesión de trabajo con July para el proyecto actual. Es el flujo normal de inicio: recuperar contexto, abrir sesión y dejar al agente listo para trabajar sin repetir onboarding innecesario.

## Cuándo se usa

- Al empezar una conversación de trabajo en un repo.
- Cuando Sergio pide recuperar contexto del proyecto.
- Cuando `/july` se invoca sin argumentos o con un objetivo.

Si Sergio pide conectar un proyecto nuevo con una primera foto del repo, usa `/july-wizard` en lugar de este flujo.

## Lo que debes hacer

Ejecuta estos pasos en orden. No muestres JSON crudo al usuario; sintetiza la respuesta.

### Paso 1 - Detectar el proyecto

Usa `project_entry` con `repo_path` apuntando al directorio de trabajo actual (`$cwd`). Esto devuelve `project_key`, estado (`new`, `partial` o `known`), superficie del repo y recomendación inicial.

### Paso 2 - Recuperar contexto

Con el `project_key` detectado:

- usa `project_context` para memoria, inbox, tareas y mejoras;
- usa `session_context` con `limit: 3` para sesiones recientes;
- usa `project_pendings` para pendientes abiertos o en progreso;
- usa `project_improvements` para mejoras abiertas, planificadas o en progreso.
- revisa `related_context.skill_suggestions` de `project_entry`;
- si Sergio indicó un objetivo, usa `proactive_recall` o `skill_suggest` con ese objetivo para recuperar skills útiles.

Si el MCP no está disponible, usa el fallback CLI equivalente desde `C:\Users\sergi\Desktop\Aplicaciones\July_unificada`.

### Paso 3 - Abrir sesión

Usa `session_start` con:

- `session_key`: `<project_key>-<YYYY-MM-DD>-<HH:MM>`;
- `project_key`: el detectado en el paso 1;
- `agent_name`: `codex` en Codex o `claude` en Claude Code;
- `goal`: el objetivo indicado por Sergio, o una frase breve si la intención está clara.

No abras varias sesiones para el mismo arranque. Si ya hay una sesión activa en el contexto actual, continúa con ella.

### Paso 4 - Presentar el arranque

Responde según el estado útil del proyecto:

**Proyecto conocido**

> Este proyecto ya tiene contexto en July. Última referencia útil: [resumen breve]. Pendientes relevantes: [lista corta]. ¿Seguimos desde ahí o vienes con una tarea nueva?

**Proyecto parcial**

> July tiene contexto parcial de este proyecto. Puedo continuar con lo recuperado o hacer un refresh selectivo de [zona que falta]. ¿Qué prefieres?

**Proyecto nuevo**

> No tengo contexto útil de este proyecto en July. Puedo hacer onboarding read-only con `/july-wizard` para guardar una primera foto, o arrancamos directamente con una tarea concreta.

Menciona mejoras abiertas solo si son relevantes para el objetivo o si Sergio pidió backlog/ideas.

Menciona skills sugeridas solo si la coincidencia es clara. Formato recomendado: "Oye Sergio, para esto quizá conviene usar `nombre-skill` porque [motivo breve]."

### Paso 5 - Esperar instrucción

No modifiques código ni ejecutes onboarding completo hasta que Sergio indique qué quiere trabajar.

## Fallback CLI mínimo

```powershell
cd C:\Users\sergi\Desktop\Aplicaciones\July_unificada
.\scripts\july.ps1 project-entry --repo-path <repo-actual>
.\scripts\july.ps1 project-context <project-key>
.\scripts\july.ps1 session-context --project <project-key> --limit 3
.\scripts\july.ps1 pendings --project-key <project-key>
.\scripts\july.ps1 improvements --project-key <project-key>
.\scripts\july.ps1 skill-suggest "<objetivo>" --project-key <project-key>
.\scripts\july.ps1 session-start <session-key> --project <project-key> --agent codex --goal "<objetivo>"
```

## Notas

- Habla siempre en español con tildes correctas.
- Si el contexto recuperado contradice el estado real del repo, dilo claramente y haz refresh selectivo antes de actuar.
- Al cerrar la sesión, usa `session_summary` y `session_end`.
