---
type: concept
status: active
created: 2026-05-08
updated: 2026-05-08
sources:
  - context/raw/2026-05-08-conversacion-wiki-codex.txt
tags:
  - flujo
  - mantenimiento
  - wiki
---

# Flujos ingest query lint

La wiki se mantiene con tres operaciones recurrentes.

## Ingest

Incorporar una nueva fuente a la memoria.

Pasos:

1. Leer la fuente.
2. Crear una pagina en `context/wiki/sources/`.
3. Extraer conceptos en `context/wiki/concepts/`.
4. Extraer entidades en `context/wiki/entities/`.
5. Guardar decisiones en `context/wiki/decisions/` si procede.
6. Actualizar `context/wiki/index.md`.
7. Registrar el cambio en `context/wiki/log.md`.

## Query

Responder usando la memoria antes de improvisar.

Pasos:

1. Leer `context/wiki/index.md`.
2. Abrir paginas relevantes.
3. Responder con base en la wiki.
4. Proponer guardar cualquier aprendizaje reutilizable.

## Lint

Mantener la wiki coherente.

Revisar:

- paginas huerfanas
- enlaces rotos
- conceptos duplicados
- contradicciones
- paginas sin frontmatter
- fuentes que no generaron conceptos o decisiones

## Relacionado

- [[Wiki persistente para Codex]]
- [[Conversacion sobre wiki persistente para Codex]]
