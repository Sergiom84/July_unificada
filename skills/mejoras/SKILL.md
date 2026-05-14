---
name: mejoras
description: Alias directo para listar, guardar o cerrar mejoras posibles de un proyecto en July. Usar cuando Sergio invoque /mejoras, pregunte por backlog de ideas o quiera guardar una posible mejora.
---

# Skill: /mejoras

Alias directo para gestionar mejoras posibles por proyecto en July. Depende del contrato base de `/july`.

## Cuándo se usa

- Sergio invoca `/mejoras`.
- Pregunta por ideas, backlog o mejoras pendientes del proyecto actual.
- Pide guardar una mejora posible sin convertirla todavía en tarea.

## Acciones

| Entrada | Acción |
|---|---|
| Sin argumentos, `listar`, `ver`, `backlog` | Lista mejoras `open`, `planned` o `in_progress` del proyecto actual. |
| `add <texto>`, `nueva <texto>`, `guardar <texto>` | Guarda una mejora posible con `project_improvement_add`. |
| `planned <id>` | Marca una mejora como `planned`. |
| `haciendo <id>`, `in_progress <id>` | Marca una mejora como `in_progress`. |
| `hecha <id>`, `done <id>` | Marca una mejora como `done`. |
| `descartar <id>`, `dismiss <id>` | Marca una mejora como `dismissed`. |

## Reglas

- Una mejora es una idea revisable. No es una tarea hasta que Sergio decida implementarla.
- Si Sergio formula trabajo ya decidido, sugiere `/pendiente <texto>` o guarda como pendiente.
- No guardes secretos, tokens, claves API, valores de `.env` ni credenciales.
- Responde con lista corta: id, estado, prioridad y título.

## Fallback CLI

```powershell
cd C:\Users\sergi\Desktop\Aplicaciones\July_unificada
.\scripts\july.ps1 improvements --repo-path <repo-actual>
.\scripts\july.ps1 improvement-add "<mejora>" --repo-path <repo-actual> --source codex
.\scripts\july.ps1 improvement-status <id> planned --repo-path <repo-actual>
.\scripts\july.ps1 improvement-status <id> done --repo-path <repo-actual>
.\scripts\july.ps1 improvement-status <id> dismissed --repo-path <repo-actual>
```
