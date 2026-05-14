---
name: pendientes
description: Alias directo para listar o actualizar pendientes de un proyecto en July. Usar cuando Sergio invoque /pendientes, pregunte qué queda por hacer o quiera ver temas abiertos.
---

# Skill: /pendientes

Alias directo para listar pendientes del proyecto actual en July. Depende del contrato base de `/july`.

## Cuándo se usa

- Sergio invoca `/pendientes`.
- Pregunta qué queda por hacer, qué temas abiertos hay o qué pendientes tiene el proyecto.
- Quiere marcar un pendiente existente como en curso o terminado.

## Acciones

| Entrada | Acción |
|---|---|
| Sin argumentos, `listar`, `ver` | Lista pendientes `pending` o `in_progress`. |
| `haciendo <id>`, `in_progress <id>` | Marca el pendiente como `in_progress`. |
| `hecho <id>`, `done <id>`, `finalizar <id>` | Marca el pendiente como `done`. |
| `add <texto>` | Recomienda `/pendiente <texto>` o guarda con `project_pending_add` si la intención es clara. |

## Reglas

- Un pendiente es trabajo por hacer y debe marcarse como `done` al completarse.
- Responde con lista corta: id, estado y título.
- Si no hay pendientes abiertos, dilo claramente y no inventes próximos pasos.
- No guardes secretos, tokens, claves API, valores de `.env` ni credenciales.

## Fallback CLI

```powershell
cd C:\Users\sergi\Desktop\Aplicaciones\July_unificada
.\scripts\july.ps1 pendings --repo-path <repo-actual>
.\scripts\july.ps1 pending-status <id> in_progress --repo-path <repo-actual>
.\scripts\july.ps1 pending-status <id> done --repo-path <repo-actual>
```
