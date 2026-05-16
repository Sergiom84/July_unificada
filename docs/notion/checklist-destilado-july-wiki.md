# Checklist: destilado July a wiki

## Cuándo ejecutarlo

Ejecutar este ritual:

- cada 5 sesiones cerradas de un mismo proyecto;
- al cerrar una iteración con decisiones técnicas o de producto importantes;
- cuando July acumule hallazgos repetidos que ya no sean solo contexto operativo;
- antes de dejar un proyecto varias semanas parado.

## Objetivo

Evitar que July sea el único lugar donde viven aprendizajes reutilizables.

July guarda estado operativo. La wiki guarda criterio curado.

## Checklist

1. Recuperar contexto operativo:
   - `project_context`;
   - `session_context` con al menos las últimas 5 sesiones;
   - pendientes y mejoras abiertas si afectan a decisiones futuras.
2. Separar señales:
   - sesión o estado puntual: se queda en July;
   - decisión estable: va a `context/wiki/decisions/`;
   - patrón reutilizable: va a `context/wiki/concepts/`;
   - investigación o comparación: va a `context/wiki/analyses/`;
   - fuente original estable: va a `context/wiki/sources/` solo si tiene valor reusable.
3. Leer `context/wiki/index.md` antes de crear páginas nuevas.
4. Actualizar páginas existentes si ya cubren el tema.
5. Crear páginas nuevas solo si reducen repetición futura.
6. Añadir wikilinks con formato `[[Nombre de página]]`.
7. Actualizar `context/wiki/index.md`.
8. Añadir entrada fechada en `context/wiki/log.md`.
9. Si algo queda dudoso, dejarlo como candidato en July, no inflar la wiki.

## Criterio de calidad

Una destilación buena permite que otro agente retome el criterio sin leer todo el historial de sesiones.

Una destilación mala copia ruido, logs o tareas efímeras.

