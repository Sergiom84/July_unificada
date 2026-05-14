---
type: log
status: active
created: 2026-05-08
updated: 2026-05-11
sources:
  - context/raw/2026-05-08-conversacion-wiki-codex.txt
  - docs/notion/patron-web-cliente.md
  - docs/notion/checklist-web-cliente.md
  - docs/notion/webs-analisis-inicial.md
tags:
  - log
  - wiki
---

# Log de la wiki

## 2026-05-08

- Instalada la estructura local de wiki en `context/`.
- Copiado `WIKI.TXT` a `context/raw/2026-05-08-conversacion-wiki-codex.txt` como primera fuente bruta.
- Creado `AGENTS.md` con instrucciones persistentes para mantener este repositorio como base procedimental.
- Ingerida la primera fuente y creadas paginas iniciales de fuente, concepto, entidad y decision.
- Ingeridos los documentos existentes de `docs/notion/` sobre webs de cliente, checklist de entrega y analisis inicial de proyectos.
- Creado el patron `docs/notion/patron-memoria-para-programar.md`.
- Registrada la decision [[Mantener memoria local por defecto]] y el analisis [[Encaje Mente_unificada y July]].
- Creado `docs/notion/prompt-arranque-proyecto.md` como prompt inicial para webs, apps y software.
- Ejecutado piloto read-only sobre MHK Studio y guardado en [[Piloto de arranque MHK Studio]].
- Corregido el prompt de arranque para usar tildes y registrada la decisión [[Español correcto con tildes]].
- Añadido `CLAUDE.md` como archivo puente para que Claude lea y aplique las reglas de `AGENTS.md`.
- Consultada la wiki para explicar Caveman, CodeBurn y Design Extract como herramientas para optimizar uso de agentes de programación.
- Aclarado que Codex también puede usar Caveman, CodeBurn y Design Extract, con diferencias entre plugin de Claude, skill de Codex y CLI.
- Instalados globalmente `codeburn` y `designlang`; instaladas skills globales de Caveman y `extract-design`; habilitados plugins de Claude Code `caveman@caveman` y `designlang@designlang`.
- Consultado el encaje entre `Mente_unificada` y `July` para diseñar una capa tipo wizard que conecte proyectos, recuerde sesiones y pregunte cuándo guardar conocimiento.
- Refinada la propuesta de July: usar una BD global única, añadir clasificación por tipo de proyecto, preferencias por proyecto y una opción de ayuda en el wizard.
- Implementado en `July` el bloque de memoria global: BD por defecto en `~/.july/july.db`, clasificación por tipo de proyecto, preferencias, acción `help`, cockpit con ayuda y skill global `july-wizard` para activar el ritual de memoria entre proyectos.
- Consultada la wiki y la skill `july-wizard` para preparar un prompt de invocación de July + Mente_unificada como copiloto de proyecto.

## 2026-05-09

- Registrada prueba inicial del prompt `july-wizard` sobre `Indalo Padel`: el agente detectó el repo como nuevo en July, lo clasificó como app móvil Flutter con backend Node/Express/PostgreSQL/Supabase, leyó instrucciones locales, sugirió skills útiles y propuso onboarding read-only sin modificar código.
- Confirmado onboarding inicial de `Indalo Padel` en July: el proyecto pasó a `known`, quedó clasificado como `mobile_app`, se creó memoria inicial, se guardó checkpoint corrigiendo la foto automática con stack real Flutter + Node/Express + PostgreSQL/Supabase y regla de no tocar `quarantine/react-vite-web/`.
- Validada recuperación en una conversación nueva de `Indalo Padel`: `july-wizard` recuperó July + Mente_unificada, recordó reglas críticas del proyecto, estado funcional conocido, pendientes/riesgos y exigió elegir tarea y leer playbook local antes de editar código.
- Consultada la wiki para valorar si conviene fusionar físicamente `Mente_unificada` y `July` en una carpeta única `July_unificada`, manteniendo la separación lógica entre memoria curada y memoria operativa.
- Creado `roadmad.md` como plan de migración por hitos para fusionar `Mente_unificada` y `July` en `July_unificada` con backups, checks y migración no destructiva.
- Ejecutado Hito 2 de la migración: creadas copias no destructivas de `Mente_unificada` y `July` en `_migration_backups/July_unificada_20260509-233901`, excluyendo `.venv`, `.env` de July y temporales.
- Ejecutado Hito 3 de la migración: preparada estructura raíz con `apps/`, `skills/`, `README.md` y actualización de `AGENTS.md` para tratar `apps/july/` como software y `context/`/`docs/` como memoria curada.
- Ejecutado Hito 4 de la migración: copiado el motor `July` dentro de `apps/july/` excluyendo `.git`, `.venv`, `.env`, `data/`, caches y bases temporales.
- Ejecutado Hito 5 de la migración: creados wrappers raíz `scripts/july.ps1`, `scripts/ui.ps1` y `scripts/mcp.ps1`; bootstrap de `apps/july` completado; tests de July OK y `project-entry` recupera `indalo-padel` como proyecto conocido desde la BD global.
- Ejecutado Hito 6 con fallback seguro: el renombrado directo de `Mente_unificada` quedó bloqueado por Windows al estar la carpeta en uso; se creó `C:\Users\sergi\Desktop\Aplicaciones\July_unificada` como copia activa verificada, con `apps/july`, wiki, wrappers, `.git` y `july-wizard` actualizado a la nueva ruta.
- Ejecutado Hito 7 de la migración: registrada la decisión [[Fusionar July y Mente_unificada en July_unificada]], actualizado el índice de la wiki y marcado `July_unificada` como carpeta activa con limpieza pendiente de `Mente_unificada` y `July` originales.
- Implementada en July la función de mejoras posibles por proyecto: tabla `project_improvements`, comandos `improvement-add`, `improvements`, `improvement-status`, herramientas MCP equivalentes, cockpit con mejoras abiertas y decisión [[Guardar mejoras posibles en July]].
- Diseñada e instalada la bóveda local cifrada para memoria sensible: July conserva solo punteros y procedimiento; `Mente_unificada` guarda payloads cifrados con DPAPI local mediante `scripts/secure-memory.ps1`.

## 2026-05-10

- Creado el atajo global `july` como skill corta para invocar July desde conversaciones nuevas con `/july`, incluyendo recuperación de contexto, registro de mejoras posibles, listado de mejoras y cierre de sesión.
- Creado el atajo global `ayuda` como skill de ayuda para recordar cómo invocar July, Caveman, Design Extract, Supabase y otras skills; añadido también `/july ayuda` como alias dentro del flujo de July.
- Aclarado en las skills `july` y `ayuda` que la capa común vive en `C:\Users\sergi\.agents\skills` para que pueda ser utilizada tanto por Claude Code como por Codex.
- Implementados pendientes por proyecto en July usando la tabla existente `tasks`: comandos `pending-add`, `pendings`, `pending-status`, herramientas MCP `project_pending_add`, `project_pendings`, `project_pending_status` y skill global `/pendiente`.
- Añadidos alias globales `/mejoras` y `/pendientes` para evitar depender de argumentos detrás de `/july` en el autocompletado de skills.
- Instalados en Mac los skills de Caveman en `.agents/skills`, habilitado el plugin `caveman@caveman` en Claude, configurado el badge de statusline y verificados `codeburn` y `designlang`.
- Consultados los riesgos de `caveman-compress` y `caveman-review`: el primero fue marcado alto por leer/escribir archivos y usar subprocess/API; el segundo medio por afectar el formato de revisiones.
- Convertido `~/.claude/skills` en Mac a symlink hacia `skills/` del repositorio y documentados en `AGENTS.md` los comandos compartidos `/July_inicio`, `/July_comprimir` y `/July_ayuda` para que Codex los trate como procedimientos locales.
- Acordado mantener los wrappers propios de July con prefijo explícito `/July_*` para distinguirlos, y conservar los nombres nativos de skills externas como `/caveman-compress`.
- Convertidos `/July_inicio`, `/July_comprimir` y `/July_ayuda` de ficheros planos a carpetas de skill con `SKILL.md` para poder instalarlos como skills globales reales.
- Renombrados los wrappers propios de July a formato estándar `july-*` (`/july-inicio`, `/july-comprimir`, `/july-ayuda`) porque Claude Code no mostraba bien los nombres con mayúscula y guion bajo.
- Añadidos los aliases `skills/july/` y `skills/july-wizard/` para que el autocompletado de Claude en Mac muestre `/july` y `/july-wizard` junto a los wrappers `july-*`, igual que en Windows.
- Cambiado `~/.claude/skills` en Mac de symlink de carpeta a directorio real con copias de las cinco skills July, porque Claude Code no las mostraba en el autocompletado aunque el symlink resolviera correctamente desde terminal.
- Añadidos `scripts/sync-claude-skills.sh` y `scripts/sync-claude-skills.ps1` para sincronizar las skills del repo a la carpeta activa de Claude sin depender de symlinks.
- Sincronizadas las cinco skills July también a `~/.codex/skills` en Mac y añadidos `scripts/sync-codex-skills.sh` y `scripts/sync-codex-skills.ps1` para que Codex pueda cargarlas en su propio selector.

## 2026-05-11

- Aclarado que Caveman aparecía en una conversación de Codex porque estaba instalado como skill de proyecto en `.agents/skills` de `July_unificada`, no como skill global de Codex; copiadas las skills de Caveman a `~/.codex/skills` en Mac para que futuras conversaciones de Codex puedan verlas globalmente tras reiniciar o abrir conversación nueva.
- Añadida la skill compartida `skills/july/SKILL.md` al repo y ampliado `/july` para guardar memorias reutilizables, punteros seguros a secretos y procedimientos detectables entre conversaciones.

## 2026-05-14

- Refinado el contrato operativo de la suite de skills July: `/july` queda como entrada principal, `/july-inicio` como arranque normal, `/july-wizard` como onboarding read-only, `/july-comprimir` como compresión segura y los aliases `/mejoras`, `/pendiente` y `/pendientes` pasan a vivir también en `skills/` como fuente de verdad sincronizable.
- Implementado el registro nativo de skills reutilizables en July: nueva tabla `skill_references`, comandos `skill-register`, `skills`, `skill-suggest`, herramientas MCP equivalentes y sugerencias `skill_suggestions` dentro de `proactive_recall`/`project_entry`; registrada `entrevistador-procesos` desde `planificador-procesos.skill` como referencia global para procesos, workflows y automatizaciones ambiguas.
