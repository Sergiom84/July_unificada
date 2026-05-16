---
name: july-destilar
description: Ritual para destilar hallazgos duraderos de July hacia la wiki curada cada pocas sesiones, evitando que la memoria operativa se acumule sin alimentar el criterio estable.
---

# Skill: /july-destilar

Usar cuando Sergio invoque `/july-destilar`, pida "destilar July a wiki", cierre varias sesiones de un proyecto o pregunte cómo mantener viva la wiki.

## Contrato

- July es memoria operativa: sesiones, estado, hallazgos, errores resueltos, pendientes y mejoras.
- `context/wiki/` es criterio curado: patrones, decisiones, análisis y fuentes reutilizables.
- La cadencia por defecto es cada 5 sesiones cerradas de un mismo proyecto.
- Si hubo una decisión importante, no esperes a la quinta sesión.
- No copies chats completos ni logs efímeros.
- No guardes secretos ni valores crudos de `.env`.

## Flujo

1. Detecta el proyecto actual con `project_entry` o el fallback CLI.
2. Recupera `project_context`, `session_context --limit 5`, pendientes y mejoras.
3. Lee `context/wiki/index.md`.
4. Clasifica cada hallazgo:
   - operativo o temporal: se queda en July;
   - decisión estable: `context/wiki/decisions/`;
   - patrón reusable: `context/wiki/concepts/`;
   - análisis o comparación: `context/wiki/analyses/`;
   - fuente reusable: `context/wiki/sources/`.
5. Actualiza páginas existentes antes de crear nuevas.
6. Si creas o cambias wiki, actualiza `context/wiki/index.md`.
7. Añade entrada a `context/wiki/log.md`.
8. Resume qué se destiló, qué quedó solo en July y qué sigue dudoso.

## Checklist base

Procedimiento largo: `docs/notion/checklist-destilado-july-wiki.md`.

## Fallback CLI

Desde `C:\Users\sergi\Desktop\Aplicaciones\July_unificada`:

```powershell
.\scripts\july.ps1 project-entry --repo-path <repo>
.\scripts\july.ps1 project-context <project-key>
.\scripts\july.ps1 session-context --project <project-key> --limit 5
.\scripts\july.ps1 pendings --repo-path <repo>
.\scripts\july.ps1 improvements --repo-path <repo>
```

