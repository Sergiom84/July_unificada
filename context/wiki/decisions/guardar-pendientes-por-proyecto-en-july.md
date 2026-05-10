---
type: decision
status: active
created: 2026-05-10
updated: 2026-05-10
sources:
  - apps/july/README.md
  - apps/july/ROADMAP.md
  - apps/july/PROJECT_PROTOCOL.md
tags:
  - july
  - pendientes
  - proyectos
  - memoria-operativa
---

# Guardar pendientes por proyecto en July

## Decisión

July debe poder guardar temas pendientes o por hacer ligados al proyecto actual y permitir cerrarlos cuando se realicen.

## Motivo

Sergio quiere poder decir durante una iteración:

> Accede a July e incluye como pendiente X.

Y más adelante preguntar:

> ¿Qué pendientes tenemos por hacer?

## Implementación esperada

- Los pendientes viven en la tabla existente `tasks`.
- Los pendientes manuales usan `task_type = manual_follow_up`.
- Se consultan por `project_key`.
- Estados: `pending`, `in_progress`, `done`.
- Un pendiente terminado debe marcarse como `done`.
- July debe exponerlos por CLI, MCP, cockpit y la skill global `/pendiente`.

## Regla

Un pendiente es trabajo decidido o recordatorio operativo por cerrar. Si solo es una idea opcional, debe guardarse como mejora posible.
