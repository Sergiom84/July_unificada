---
type: source
status: active
created: 2026-05-08
updated: 2026-05-08
sources:
  - context/raw/2026-05-08-conversacion-wiki-codex.txt
tags:
  - codex
  - wiki
  - procedimiento
---

# Conversacion sobre wiki persistente para Codex

## Resumen

La fuente recoge una conversacion sobre como crear una wiki persistente mantenida por Codex para evitar repetir contexto en cada sesion.

La propuesta original se basa en tres capas:

- fuentes brutas inmutables en `raw/`
- wiki generada y mantenida por Codex en `wiki/`
- instrucciones persistentes mediante `AGENTS.md`

La conversacion tambien propone flujos recurrentes de trabajo:

- ingest: incorporar nuevas fuentes
- query: consultar la wiki antes de responder o programar
- lint: mantener la wiki limpia y detectar contradicciones

## Ideas principales

- Codex puede funcionar mejor si tiene una memoria local estructurada.
- La memoria no debe ser una carpeta caotica de documentos, sino una wiki mantenida.
- Las fuentes originales deben conservarse sin modificar.
- Las paginas generadas deben estar interconectadas con wikilinks.
- `AGENTS.md` debe fijar reglas operativas para que Codex mantenga la estructura.
- Obsidian puede usarse como visor opcional, pero no es obligatorio.
- Cuando la wiki crezca, se puede considerar busqueda local avanzada; no hace falta al principio.

## Elementos reutilizables

- [[Wiki persistente para Codex]]
- [[Flujos ingest query lint]]
- [[Usar wiki local en este proyecto]]
- [[Codex]]

## Adaptacion a este proyecto

En este proyecto se ha elegido instalar la wiki localmente porque el repositorio contiene procedimientos, no codigo. La estructura `context/` queda como memoria activa y `docs/notion/` queda para documentos mas pulidos.

## Fuente

- `context/raw/2026-05-08-conversacion-wiki-codex.txt`
