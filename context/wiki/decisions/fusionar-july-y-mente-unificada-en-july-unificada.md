---
type: decision
status: active
created: 2026-05-09
updated: 2026-05-16
sources:
  - roadmap.md
  - C:/Users/sergi/Desktop/Aplicaciones/July/README.md
  - context/wiki/analyses/encaje-mente-unificada-y-july.md
tags:
  - july
  - mente-unificada
  - arquitectura
  - migracion
---

# Fusionar July y Mente_unificada en July_unificada

## Decisión

Unificar físicamente `Mente_unificada` y `July` en una carpeta operativa llamada `July_unificada`.

La separación conceptual se mantiene:

| Capa | Ubicación | Función |
| --- | --- | --- |
| Memoria curada | `context/` y `docs/` | Procedimientos, decisiones, patrones y wiki revisable |
| Motor operativo | `apps/july/` | July, CLI, MCP, cockpit, sesiones, recall y project context |
| Skills y rituales | `skills/` y skills globales | Comportamiento reutilizable para agentes |

## Motivo

La prueba con `Indalo Padel` validó que July puede actuar como memoria operativa y que `Mente_unificada` aporta criterio curado. Mantener ambas capas en carpetas separadas generaba fricción de rutas y duplicaba el esfuerzo mental para Sergio.

## Resultado aplicado

- Creada carpeta activa `C:\Users\sergi\Desktop\Aplicaciones\July_unificada`.
- Copiado `July` dentro de `apps/july/`.
- Conservados `context/` y `docs/` como memoria curada.
- Creados wrappers raíz en `scripts/`.
- Actualizada la skill global `july-wizard` para usar la nueva ruta.
- Verificado que July lee la BD global y que `indalo-padel` aparece como proyecto conocido.
- Archivada la raíz antigua `Mente_unificada` en `_migration_backups/archived-original-roots-20260516-2255/`.
- Confirmado que `July` original no existe ya como carpeta activa en `C:\Users\sergi\Desktop\Aplicaciones`.

## Cierre

El renombrado directo de `Mente_unificada` quedó bloqueado por Windows porque la carpeta estaba en uso. Por seguridad, no se forzó.

La limpieza final se cerró el 2026-05-16 archivando la raíz antigua sin borrarla. `July_unificada` queda como única raíz activa.

## Regla

`July_unificada` es la carpeta activa. Las carpetas anteriores son respaldo histórico, no fuente de trabajo.
