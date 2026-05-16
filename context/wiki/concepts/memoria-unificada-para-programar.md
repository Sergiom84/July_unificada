---
type: concept
status: active
created: 2026-05-08
updated: 2026-05-16
sources:
  - docs/notion/patron-memoria-para-programar.md
  - C:/Users/sergi/Desktop/Aplicaciones/July/README.md
  - C:/Users/sergi/Desktop/Aplicaciones/July/PROJECT_PROTOCOL.md
tags:
  - memoria
  - programacion
  - july
  - codex
---

# Memoria unificada para programar

Patron para conectar una memoria curada en Markdown con una memoria operativa por sesiones y proyectos.

## Capas

| Capa | Herramienta | Funcion |
| --- | --- | --- |
| Memoria curada | `July_unificada/context` y `July_unificada/docs` | Procedimientos, patrones, decisiones y wiki revisable |
| Memoria operativa | `apps/july` + `C:\Users\sergi\.july\july.db` | Sesiones, project context, recall, topic keys y cockpit local |
| Proyecto real | app, web o repo | Codigo, README, AGENTS.md local y decisiones especificas |

## Criterio

La wiki no debe guardar todo. Debe guardar conocimiento que mejore futuras decisiones o evite repetir trabajo.

July puede registrar el hilo operativo de una sesion. Cuando algo se vuelve estable, se destila a `context/wiki/`.

## Flujo recomendado

1. Abrir Codex en el proyecto con acceso adicional a `July_unificada`.
2. Leer instrucciones locales del proyecto.
3. Leer `July_unificada/context/wiki/index.md`.
4. Recuperar contexto de July si esta disponible.
5. Trabajar sobre el proyecto.
6. Guardar decisiones duraderas y errores resueltos.
7. Ejecutar [[Ritual de destilado July a wiki]] cada 5 sesiones cerradas o cuando haya una decisión fuerte.
8. Destilar patrones reutilizables a la wiki curada.

## Relacionado

- [[Wiki persistente para Codex]]
- [[Flujos ingest query lint]]
- [[Ritual de destilado July a wiki]]
- [[Mantener memoria local por defecto]]
