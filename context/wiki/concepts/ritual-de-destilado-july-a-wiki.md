---
type: concept
status: active
created: 2026-05-16
updated: 2026-05-16
sources:
  - AGENTS.md
  - docs/notion/checklist-destilado-july-wiki.md
tags:
  - july
  - wiki
  - memoria
  - ritual
---

# Ritual de destilado July a wiki

El ritual de destilado evita que July acumule hallazgos operativos sin alimentar la wiki curada.

## Regla

Cada 5 sesiones cerradas de un proyecto, o antes si aparece una decisión fuerte, el agente debe revisar July y mover a `context/wiki/` solo lo que tenga valor estable y reutilizable.

## Separación

| Tipo de información | Destino |
| --- | --- |
| Estado de sesión, pendiente puntual, mejora en revisión | July |
| Decisión estable | `context/wiki/decisions/` |
| Patrón reutilizable | `context/wiki/concepts/` |
| Comparación o investigación | `context/wiki/analyses/` |
| Fuente original reusable | `context/wiki/sources/` |

## Criterio práctico

La wiki no debe guardar todo lo que ocurre. Debe guardar lo que evita repetir criterio en futuras sesiones.

El procedimiento operativo vive en [Checklist: destilado July a wiki](../../../docs/notion/checklist-destilado-july-wiki.md) y la skill ejecutable es `/july-destilar`.

