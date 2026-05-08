---
type: concept
status: active
created: 2026-05-08
updated: 2026-05-08
sources:
  - context/raw/2026-05-08-conversacion-wiki-codex.txt
tags:
  - codex
  - wiki
  - memoria
---

# Wiki persistente para Codex

Una wiki persistente para Codex es una base de conocimiento local que convierte fuentes brutas y conversaciones en paginas estructuradas, enlazadas y mantenidas por el agente.

## Para que sirve

- Reducir repeticion de contexto entre sesiones.
- Guardar decisiones y reglas de trabajo.
- Convertir conversaciones utiles en procedimientos reutilizables.
- Mantener una memoria revisable por Sergio.
- Dar a Codex contexto estable antes de responder o ejecutar tareas.

## Capas

| Capa | Carpeta | Funcion |
| --- | --- | --- |
| Fuente bruta | `context/raw/` | Material original, no editado |
| Wiki activa | `context/wiki/` | Resumenes, conceptos, entidades, decisiones y analisis |
| Instrucciones | `AGENTS.md` | Reglas para mantener la wiki |

## Regla clave

No todo se guarda. Solo se destila lo que pueda ahorrar tiempo, evitar errores o mejorar decisiones futuras.

## Relacionado

- [[Flujos ingest query lint]]
- [[Usar wiki local en este proyecto]]
- [[Conversacion sobre wiki persistente para Codex]]
