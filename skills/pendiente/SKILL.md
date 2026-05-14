---
name: pendiente
description: Alias directo para guardar, listar o cerrar temas pendientes por proyecto en July. Usar cuando Sergio invoque /pendiente, pida añadir, ver, avanzar o finalizar un pendiente del proyecto actual.
---

# Skill: /pendiente

Alias directo para gestionar un pendiente concreto del proyecto actual en July. Depende del contrato base de `/july`.

## Cuándo se usa

- Sergio invoca `/pendiente`.
- Pide guardar algo como pendiente, por hacer o tema abierto.
- Pide marcar un pendiente como en curso o terminado.

## Acciones

| Entrada | Acción |
|---|---|
| `<texto>`, `add <texto>`, `guardar <texto>` | Guarda un pendiente nuevo con `project_pending_add`. |
| `listar`, `lista`, `ver` | Lista pendientes abiertos o en progreso. |
| `haciendo <id>`, `in_progress <id>` | Marca el pendiente como `in_progress`. |
| `hecho <id>`, `done <id>`, `finalizar <id>` | Marca el pendiente como `done`. |

## Reglas

- Un pendiente es trabajo decidido o recordatorio operativo por cerrar.
- Si es solo una idea opcional, usa `/mejoras add <texto>` o `/july mejora <texto>`.
- Si Sergio dice que ya está realizado, marca el pendiente como `done`; no crees uno nuevo.
- No guardes secretos, tokens, claves API, valores de `.env` ni credenciales.

## Fallback CLI

```powershell
cd C:\Users\sergi\Desktop\Aplicaciones\July_unificada
.\scripts\july.ps1 pending-add "<pendiente>" --repo-path <repo-actual> --source codex
.\scripts\july.ps1 pendings --repo-path <repo-actual>
.\scripts\july.ps1 pending-status <id> in_progress --repo-path <repo-actual>
.\scripts\july.ps1 pending-status <id> done --repo-path <repo-actual>
```
