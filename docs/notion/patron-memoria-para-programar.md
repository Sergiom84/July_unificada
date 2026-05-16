# Patron: Memoria unificada para programar mejor

## Objetivo

Usar una memoria local compartida para que Codex, July y los proyectos de Sergio trabajen con contexto acumulado, sin repetir decisiones, errores, patrones ni explicaciones en cada sesion.

## Principio base

La memoria debe ser local-first.

Por defecto, nada se sube a Notion, Google Drive, GitHub ni servicios externos. Solo se usa una integracion externa cuando Sergio lo pida de forma explicita.

## Capas del sistema

| Capa | Ubicacion | Funcion |
| --- | --- | --- |
| Memoria curada | `C:\Users\sergi\Desktop\Aplicaciones\July_unificada\context` y `docs` | Procedimientos, patrones, decisiones y wiki Markdown revisable |
| Memoria operativa | `C:\Users\sergi\Desktop\Aplicaciones\July_unificada\apps\july` + `C:\Users\sergi\.july\july.db` | Sesiones, contexto por proyecto, recall, topic keys y cockpit local |
| Proyecto concreto | cada app, web o repo | Codigo real, README, AGENTS.md propio, decisiones locales |

## Papel de la wiki curada

La wiki de `July_unificada` es el segundo cerebro curado.

Debe guardar:

- patrones repetibles;
- decisiones consolidadas;
- checklists;
- procedimientos;
- aprendizajes que sirvan entre proyectos;
- analisis destilados desde conversaciones o proyectos.

No debe convertirse en un volcado de chats completos.

## Papel de July

`July` es la memoria operativa y dinamica.

Debe guardar:

- sesiones de trabajo;
- estado de un proyecto;
- hallazgos durante una iteracion;
- errores resueltos;
- topic keys transversales;
- contribuciones de modelos;
- contexto recuperable por proyecto.

July no sustituye a la wiki curada. Cuando algo se vuelve estable y reutilizable, se destila hacia `context/wiki/`.

## Papel de cada proyecto

Cada proyecto debe tener, cuando sea util, un `AGENTS.md` propio que indique:

- que es el proyecto;
- comandos reales;
- stack;
- reglas locales;
- enlace a la memoria compartida;
- criterio para guardar decisiones.

Plantilla minima:

```md
# Project Instructions

## Memoria compartida

La memoria curada vive en:

`C:\Users\sergi\Desktop\Aplicaciones\July_unificada`

Antes de tomar decisiones tecnicas, producto o arquitectura, revisar:

- `context/wiki/index.md`
- paginas relevantes de `context/wiki/concepts/`
- paginas relevantes de `context/wiki/decisions/`

Si July esta disponible, usarlo como memoria operativa de sesion:

- recuperar contexto previo del proyecto;
- registrar decisiones duraderas;
- guardar errores resueltos;
- cerrar la sesion con resumen y siguientes pasos.

## Regla local

No guardar secretos, claves ni valores crudos de `.env` en la memoria compartida.
```

## Como abrir Codex con memoria compartida

Desde un proyecto concreto:

```powershell
codex --cd "C:\ruta\al\proyecto" --add-dir "C:\Users\sergi\Desktop\Aplicaciones\July_unificada"
```

Esto permite a Codex trabajar en el proyecto y leer la memoria compartida.

## Flujo al entrar en un proyecto

1. Leer `AGENTS.md` del proyecto si existe.
2. Leer `README.md` o documentacion base del proyecto.
3. Leer `July_unificada/context/wiki/index.md`.
4. Abrir paginas relevantes de conceptos y decisiones.
5. Si July esta disponible, recuperar contexto operativo del proyecto.
6. Antes de programar, resumir:
   - que es el proyecto;
   - que contexto previo importa;
   - que decision o patron puede reutilizarse.

## Flujo durante el trabajo

Guardar solo conocimiento durable:

- decision tecnica tomada;
- error resuelto y causa;
- patron que se puede repetir;
- riesgo detectado;
- contrato entre frontend/backend;
- comando o configuracion importante;
- cambio de arquitectura;
- aprendizaje que evita repetir trabajo.

No guardar:

- logs sin conclusion;
- tareas triviales de minutos;
- secretos;
- detalles que ya se deducen facilmente del repo;
- pensamientos no adoptados.

## Flujo de cierre

Al terminar una sesion:

1. Resumir que se hizo.
2. Apuntar que queda pendiente.
3. Guardar en July el estado operativo si se esta usando.
4. Ejecutar `/july-destilar` cada 5 sesiones cerradas o antes si hubo decisiones fuertes.
5. Destilar hacia `context/wiki/` solo las reglas o decisiones reutilizables.
6. Actualizar `context/wiki/log.md` si se modifico la wiki.

## Regla de oro

July recuerda la sesion.  
La wiki conserva el criterio.
