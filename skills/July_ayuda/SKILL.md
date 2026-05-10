---
name: July_ayuda
description: Muestra una chuleta rápida de comandos y herramientas disponibles para July, Caveman y skills habituales. Usar cuando Sergio invoque /July_ayuda o pregunte cómo llamar los comandos propios de July.
---

# Skill: /July_ayuda

Muestra una chuleta rápida de todos los comandos y herramientas disponibles en este entorno.

## Lo que debes hacer

Responde con este resumen formateado. No busques nada, no llames herramientas: solo muestra esto.

---

## Comandos disponibles

### Sesión y memoria (July)
| Comando | Qué hace |
|---|---|
| `/July_inicio` | Arranca sesión, recupera contexto del proyecto desde July |
| `/July_inicio <objetivo>` | Igual, pero con un objetivo concreto registrado |

### Ficheros y tokens
| Comando | Qué hace |
|---|---|
| `/July_comprimir <fichero>` | Comprime un fichero largo con Caveman (con verificación de seguridad) |

### Ayuda
| Comando | Qué hace |
|---|---|
| `/July_ayuda` | Esta pantalla |

---

## Herramientas siempre disponibles (sin comando)

**July MCP** - disponible en toda conversación, invócalo por nombre:
- "guarda esto en July"
- "¿qué quedó pendiente en este proyecto?"
- "abre sesión en July para indalo-padel"
- "añade esto como mejora posible"

**Caveman** - para conversaciones largas:
- `/July_comprimir` para comprimir un fichero de procedimientos
- `/caveman-compress` sigue siendo el comando nativo de Caveman
- Caveman-review se activa automáticamente en revisiones de código

**Otros skills de Anthropic** disponibles con `/`:
- `/review` - revisión de pull request
- `/init` - inicializar CLAUDE.md en un proyecto nuevo
- `/security-review` - revisión de seguridad de cambios pendientes

---

## Reglas de oro

1. Archivos sensibles (`.env`, claves, `context/secure/`) -> nunca a Caveman
2. Proyecto conocido -> `/July_inicio` al empezar
3. Conversación larga -> `/July_comprimir` el fichero de contexto más pesado
4. Duda sobre qué hace July -> pregunta directamente, tiene 30+ herramientas MCP

---

*Reinicia Claude Code si un comando nuevo no aparece en el autocompletado.*
