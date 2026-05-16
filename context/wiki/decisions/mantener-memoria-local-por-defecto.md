---
type: decision
status: active
created: 2026-05-08
updated: 2026-05-16
sources:
  - docs/notion/patron-memoria-para-programar.md
tags:
  - decision
  - privacidad
  - local-first
---

# Mantener memoria local por defecto

## Contexto

Sergio quiere que la memoria de trabajo funcione como segundo cerebro entre proyectos, pero prefiere que la informacion quede en local y no se suba a Notion ni otros servicios externos por defecto.

## Decision

La memoria de `July_unificada` se mantiene local-first: wiki curada en Markdown, motor July en local y base viva en `C:\Users\sergi\.july\july.db`. No se usa Notion, Google Drive, GitHub ni otro servicio externo salvo peticion explicita.

## Motivo

La memoria puede contener decisiones, detalles de clientes, rutas locales, arquitectura, problemas tecnicos y contexto de trabajo. Mantenerla local reduce exposicion y conserva control.

## Consecuencias practicas

- `docs/notion/` es solo una carpeta local con Markdown curado.
- Usar conectores externos requiere confirmacion explicita.
- No guardar secretos, claves ni valores crudos de `.env`.
- Si en el futuro se sincroniza o publica algo, debe hacerse con un filtro claro.

## Relacionado

- [[Memoria unificada para programar]]
- [[Wiki persistente para Codex]]
