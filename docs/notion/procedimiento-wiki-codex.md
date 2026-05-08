# Procedimiento: Wiki persistente para Codex

## Objetivo

Crear una memoria de trabajo mantenida por Codex para no repetir contexto en cada sesion y convertir conversaciones, decisiones y aprendizajes en conocimiento reutilizable.

La idea base es separar tres capas:

- `raw/`: fuentes originales que no se editan.
- `wiki/`: paginas mantenidas por Codex a partir de esas fuentes.
- `AGENTS.md`: instrucciones que explican a Codex como leer, actualizar y mantener la wiki.

## Decision inicial

Para empezar, usar una wiki dentro de este repositorio en vez de montar una wiki global separada.

Motivo:

- Ya existe documentacion reutilizable en `docs/notion/`.
- El procedimiento todavia esta en fase de ajuste.
- Evita configurar demasiadas piezas antes de validar el habito.

Estructura propuesta:

```text
context/
  raw/
    assets/
  wiki/
    index.md
    log.md
    sources/
    entities/
    concepts/
    decisions/
    analyses/
```

Cuando el flujo este consolidado, se puede mover o duplicar a una wiki global como `C:\Users\sergi\codex-wiki` y usar `codex --add-dir` desde varios proyectos.

## Roles de cada carpeta

`context/raw/` es la fuente de verdad. Aqui van conversaciones exportadas, articulos, PDFs convertidos a texto, notas de cliente, decisiones copiadas desde Notion y material bruto.

Regla: no editar ni borrar nada de `raw/` salvo peticion explicita.

`context/wiki/` es la memoria viva. Codex puede crear y modificar paginas aqui.

Regla: cada cambio importante debe actualizar `index.md` y dejar rastro en `log.md`.

`docs/notion/` mantiene documentos curados para Notion o para procesos ya bastante estables.

Regla: usar `docs/notion/` para procedimientos limpios; usar `context/wiki/` para memoria incremental y trabajo en curso.

## Flujo 1: Ingestar informacion

Usar cuando aparezca una nueva fuente que pueda ser reutilizable.

Ejemplos:

- Conversacion importante con ChatGPT o Codex.
- Analisis de una web de cliente.
- Decision tecnica.
- Checklist que haya salido de un proyecto.
- Error recurrente y su solucion.

Prompt recomendado:

```text
Ingiere context/raw/NOMBRE_DEL_ARCHIVO siguiendo el procedimiento de la wiki.

Quiero que:
1. crees o actualices una pagina en context/wiki/sources/
2. extraigas conceptos reutilizables en context/wiki/concepts/
3. extraigas entidades relevantes en context/wiki/entities/
4. guardes decisiones o reglas en context/wiki/decisions/ si procede
5. actualices context/wiki/index.md
6. anadas una entrada a context/wiki/log.md
```

## Flujo 2: Consultar antes de programar

Usar antes de una tarea que dependa de decisiones anteriores, patrones propios o reglas de trabajo.

Prompt recomendado:

```text
Antes de modificar procedimientos o documentos, lee context/wiki/index.md y las paginas relevantes.
Despues aplica la tarea usando ese contexto.
Si aparece una decision reutilizable, propon donde guardarla en la wiki.
```

## Flujo 3: Guardar una decision

Usar al cerrar una conversacion o despues de resolver algo que conviene recordar.

Prompt recomendado:

```text
Guarda esta decision en context/wiki/decisions/.
Incluye:
- contexto
- decision tomada
- motivo
- consecuencias practicas
- enlaces a fuentes o archivos relacionados

Actualiza context/wiki/index.md y context/wiki/log.md.
```

## Flujo 4: Mantenimiento

Usar cada cierto tiempo, no en cada tarea.

Prompt recomendado:

```text
Haz un lint de context/wiki/.
Busca:
- paginas huerfanas
- enlaces rotos
- conceptos duplicados
- decisiones contradictorias
- fuentes sin reflejo en conceptos o decisiones
- paginas sin frontmatter

Primero dame el informe. No apliques cambios hasta que lo confirme.
```

## Convenciones de pagina

Cada pagina generada en `context/wiki/` debe empezar con frontmatter:

```yaml
---
type: source | entity | concept | decision | analysis | index | log
status: draft | active | needs-review | superseded
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources:
  - context/raw/archivo.md
tags:
  - ejemplo
---
```

Usar enlaces tipo Obsidian:

```text
[[Nombre de pagina]]
```

## Reglas practicas para Sergio

- No intentar documentarlo todo.
- Guardar solo lo que vaya a ahorrar tiempo o errores despues.
- Las decisiones importantes van a `decisions/`.
- Los patrones repetibles van a `concepts/`.
- Los documentos originales van a `raw/`.
- Las respuestas largas de IA no se convierten enteras en wiki; se destilan.
- Si una regla ya esta madura, se puede mover a `docs/notion/` o a `AGENTS.md`.

## Diferencias respecto a la propuesta inicial

- Se adapta a Windows y a este repositorio.
- Evita crear una wiki global antes de validar el habito.
- Mantiene separado `docs/notion/` de la memoria incremental.
- Usa `AGENTS.md` como contrato activo para que Codex mantenga la wiki.
- Usa `codex --add-dir` solo como paso futuro para compartir una wiki entre proyectos.

## Estado de instalacion

Instalado el 2026-05-08.

Estructura creada:

```text
context/raw/assets/
context/wiki/sources/
context/wiki/entities/
context/wiki/concepts/
context/wiki/decisions/
context/wiki/analyses/
context/wiki/index.md
context/wiki/log.md
```

Primera fuente ingerida:

```text
context/raw/2026-05-08-conversacion-wiki-codex.txt
```

Paginas iniciales creadas:

- `context/wiki/sources/2026-05-08-conversacion-wiki-codex.md`
- `context/wiki/concepts/wiki-persistente-para-codex.md`
- `context/wiki/concepts/flujos-ingest-query-lint.md`
- `context/wiki/entities/codex.md`
- `context/wiki/decisions/usar-wiki-local-en-este-proyecto.md`
