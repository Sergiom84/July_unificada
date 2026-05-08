---
type: decision
status: active
created: 2026-05-08
updated: 2026-05-08
sources:
  - docs/notion/patron-web-cliente.md
  - docs/notion/webs-analisis-inicial.md
tags:
  - decision
  - ia
  - chatbot
  - web-cliente
---

# Usar IA solo cuando aporta

## Contexto

Algunas webs pueden incorporar IA o chatbot, pero no todas lo necesitan. Lucy Lara lo usa como parte de una plantilla avanzada, mientras que Zaidy y MHK Studio no lo necesitan de inicio.

## Decision

No meter IA por defecto. Usarla solo cuando mejore captacion, soporte o consulta de catalogo.

## Motivo

La IA anade complejidad tecnica, fuentes de conocimiento, costes, prompts, validacion y mantenimiento. Solo compensa si resuelve un caso real del cliente.

## Consecuencias practicas

- Definir fuente de conocimiento antes de construir chatbot.
- Separar prompt de datos de negocio.
- Validar respuestas contra datos reales.
- Registrar problemas y soluciones.
- Si se usa Supabase en produccion, recordar el pooler para la conexion.

## Relacionado

- [[Lucy Lara]]
- [[Web de cliente para captacion]]
- [[Analisis inicial de webs de cliente]]
