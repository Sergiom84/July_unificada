---
type: analysis
status: active
created: 2026-05-08
updated: 2026-05-08
sources:
  - docs/notion/patron-memoria-para-programar.md
  - C:/Users/sergi/Desktop/Aplicaciones/July/README.md
  - C:/Users/sergi/Desktop/Aplicaciones/July/ROADMAP.md
  - C:/Users/sergi/Desktop/Aplicaciones/July/PROJECT_PROTOCOL.md
tags:
  - july
  - mente-unificada
  - arquitectura
---

# Encaje Mente_unificada y July

## Sintesis

`Mente_unificada` y July no compiten. Cubren dos niveles distintos de memoria.

`Mente_unificada` debe ser la memoria curada: procedimientos, patrones, decisiones y wiki Markdown revisable.

July debe ser la memoria operativa: sesiones, contexto por proyecto, topic keys, recall, trazabilidad de modelos y cockpit local.

## Separacion recomendada

| Necesidad | Mejor lugar |
| --- | --- |
| Procedimiento estable | `Mente_unificada/docs/notion/` |
| Concepto reutilizable | `Mente_unificada/context/wiki/concepts/` |
| Decision consolidada | `Mente_unificada/context/wiki/decisions/` |
| Estado de una sesion | July |
| Contexto vivo de un proyecto | July |
| Error resuelto durante una iteracion | July primero; wiki si se vuelve patron |
| Checklist reusable | `Mente_unificada` |

## Riesgo principal

El riesgo es duplicar memoria sin criterio: guardar lo mismo en July, wiki, Notion y documentos sueltos.

## Regla practica

July recuerda la sesion. Mente_unificada conserva el criterio.

## Relacionado

- [[Memoria unificada para programar]]
- [[Mantener memoria local por defecto]]
- [[Usar wiki local en este proyecto]]
