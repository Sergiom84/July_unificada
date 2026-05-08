---
type: decision
status: active
created: 2026-05-08
updated: 2026-05-08
sources:
  - context/raw/2026-05-08-conversacion-wiki-codex.txt
tags:
  - decision
  - wiki
  - procedimientos
---

# Usar wiki local en este proyecto

## Contexto

Sergio quiere integrar un nuevo procedimiento de trabajo para que Codex tenga memoria y no haya que repetir contexto constantemente.

El proyecto actual no contiene una aplicacion de programacion. Contiene procedimientos que Sergio quiere ordenar, integrar y convertir en memoria reutilizable.

## Decision

Instalar la wiki persistente dentro de este proyecto usando la carpeta `context/`.

## Motivos

- El proyecto ya funciona como base de procedimientos.
- Permite validar el habito antes de crear una wiki global compartida.
- Evita mezclar fuentes brutas con documentos curados.
- Mantiene `docs/notion/` como salida limpia para procedimientos maduros.
- Permite que Codex cargue reglas persistentes desde `AGENTS.md`.

## Consecuencias practicas

- Las fuentes nuevas deben ir a `context/raw/`.
- Las paginas mantenidas por Codex deben ir a `context/wiki/`.
- Las instrucciones operativas viven en `AGENTS.md`.
- Los procedimientos ya limpios pueden vivir en `docs/notion/`.
- Si mas adelante hace falta compartir memoria con otros proyectos, se podra crear una wiki global y acceder a ella con `codex --add-dir`.

## Relacionado

- [[Wiki persistente para Codex]]
- [[Flujos ingest query lint]]
- [[Conversacion sobre wiki persistente para Codex]]
