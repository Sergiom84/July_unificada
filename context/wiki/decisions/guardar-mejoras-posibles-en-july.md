---
type: decision
status: active
created: 2026-05-09
updated: 2026-05-09
sources:
  - apps/july/README.md
  - apps/july/ROADMAP.md
  - apps/july/PROJECT_PROTOCOL.md
tags:
  - july
  - mejoras
  - proyectos
  - memoria-operativa
---

# Guardar mejoras posibles en July

## Decisión

July debe poder guardar ideas o posibles mejoras ligadas al proyecto actual sin convertirlas automáticamente en tareas ni decisiones.

## Motivo

Sergio quiere poder decir durante una iteración:

> Accede a July e incluye como posible mejora X.

Y más adelante preguntar:

> ¿Tenemos alguna mejora por implementar?

## Implementación esperada

- Las mejoras viven en la tabla `project_improvements`.
- Se consultan por `project_key`.
- Estados: `open`, `planned`, `in_progress`, `done`, `dismissed`.
- Prioridades: `low`, `normal`, `high`.
- July debe recuperarlas en `project-context`, MCP y cockpit.

## Regla

Una mejora posible es una idea revisable. No es una tarea hasta que Sergio decida implementarla. No es una decisión hasta que se adopte como criterio.
