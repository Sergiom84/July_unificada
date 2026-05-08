---
type: entity
status: active
created: 2026-05-08
updated: 2026-05-08
sources:
  - context/raw/2026-05-08-conversacion-wiki-codex.txt
tags:
  - herramienta
  - openai
  - codex
---

# Codex

Codex es la herramienta que Sergio usa como agente de trabajo para leer archivos, modificar documentos, ejecutar comandos y mantener esta base procedimental.

## Uso en este proyecto

En este repositorio, Codex debe actuar como mantenedor de procedimientos y memoria, no como agente centrado en codigo.

Responsabilidades:

- leer fuentes en `context/raw/`
- mantener paginas en `context/wiki/`
- respetar `AGENTS.md`
- actualizar indice y log despues de cambios relevantes
- convertir conversaciones utiles en conocimiento reutilizable

## Relacionado

- [[Wiki persistente para Codex]]
- [[Flujos ingest query lint]]
- [[Usar wiki local en este proyecto]]
