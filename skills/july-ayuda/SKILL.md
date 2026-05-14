---
name: july-ayuda
description: Muestra una chuleta rápida de comandos, roles de skills y reglas de uso para July, Caveman y memoria local. Usar cuando Sergio invoque /july-ayuda o pregunte cómo usar July y sus skills dependientes.
---

# Skill: /july-ayuda

Muestra una chuleta rápida. No busques nada ni llames herramientas: solo responde con el resumen.

---

## July: uso recomendado

| Comando | Cuándo usarlo |
|---|---|
| `/july` | Entrada principal: recuperar contexto, arrancar sesión o enrutar una acción. |
| `/july <objetivo>` | Igual, pero registra el objetivo de trabajo. |
| `/july-inicio` | Arranque normal de proyecto conocido o parcialmente conocido. |
| `/july-wizard` | Onboarding read-only de proyecto nuevo o contexto insuficiente. |
| `/july guarda <texto>` | Guardar memoria reutilizable del proyecto actual. |
| `/july mejora <texto>` | Guardar una idea revisable, no trabajo decidido. |
| `/july pendiente <texto>` | Guardar trabajo decidido o recordatorio operativo por cerrar. |
| `/july pendientes` | Ver pendientes abiertos o en progreso. |
| `/july mejoras` | Ver mejoras abiertas, planificadas o en progreso. |
| `/july secreto <texto>` | Guardar solo puntero/procedimiento seguro, nunca el secreto. |
| `/july registrar skill <ruta>` | Registrar una skill local para que July pueda sugerirla en otros proyectos. |
| `/july qué skill sirve para <X>` | Buscar en skills registradas una herramienta útil para esa tarea. |
| `/july cuál era la skill que hacía <Y>` | Recuperar una skill por función o recuerdo aproximado. |
| `/july cierra` | Guardar resumen y cerrar sesión July. |

## Aliases directos

Si están instalados:

| Comando | Qué hace |
|---|---|
| `/mejoras` | Lista o gestiona mejoras posibles del proyecto actual. |
| `/pendiente <texto>` | Crea, actualiza o cierra un pendiente. |
| `/pendientes` | Lista pendientes abiertos o en progreso. |

## Ficheros y tokens

| Comando | Qué hace |
|---|---|
| `/july-comprimir <fichero>` | Comprime un fichero largo con verificación previa de seguridad. |
| `/caveman-compress <fichero>` | Comando nativo de Caveman; úsalo solo cuando no necesites la capa segura de July. |

## Skills sugeridas por July

July puede guardar referencias a skills locales y sugerirlas cuando el objetivo encaje. Ejemplo: si el trabajo empieza con "quiero crear una automatización, pero no tengo claro el proceso", July puede recordar `entrevistador-procesos` antes de construir.

También puedes preguntar en lenguaje natural:

- "Oye July, quiero hacer X, ¿tenemos alguna skill que me ayude?"
- "Oye July, ¿cuál era la skill que hacía Y?"

## Reglas de memoria

| Tipo | Dónde va |
|---|---|
| Estado de sesión, errores resueltos, decisiones de iteración | July |
| Mejoras posibles y pendientes | July |
| Patrones reutilizables entre proyectos | `context/wiki/` o `docs/notion/` |
| Secretos, tokens, claves API | Nunca en July ni en la wiki; solo punteros seguros |

## Reglas de oro

1. Proyecto conocido: usa `/july` o `/july-inicio`.
2. Proyecto nuevo: usa `/july-wizard` y confirma onboarding read-only antes de guardar.
3. Idea opcional: mejora.
4. Trabajo decidido: pendiente.
5. Criterio adoptado: memoria o decisión curada, según alcance.
6. Conversación larga o fichero pesado: `/july-comprimir`.
7. Si hay duda de seguridad, no guardes el contenido; guarda solo el puntero.

---

*Si una skill nueva no aparece en autocompletado, sincroniza desde `skills/` y reinicia el selector de la herramienta.*
