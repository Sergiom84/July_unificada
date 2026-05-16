# July

July es un orquestador local-first con memoria persistente. Su funcion no es solo guardar entradas libres, sino entender en que proyecto o conversacion esta trabajando, capturar avances, relacionarlos entre proyectos y servir contexto reutilizable a distintos agentes y clientes para no repetir trabajo ni dar pasos atras entre iteraciones.

## Lectura obligatoria para agentes

Antes de actuar sobre este proyecto, cualquier agente, CLI o modelo debe leer en este orden:

1. `README.md`
2. `ROADMAP.md`
3. `AGENTS.md`
4. `PROJECT_PROTOCOL.md` cuando la tarea toque comportamiento dentro de proyectos o integraciones reales
5. Los archivos especificos del area que vaya a tocar

Ningun agente debe asumir que el chat actual sustituye a estos documentos.

## Mantenimiento documental obligatorio

Si un cambio modifica comandos, arquitectura, flujo MCP, proveedor LLM, prioridades, roadmap o la forma de trabajar del proyecto, ese mismo cambio debe actualizar `README.md` y `ROADMAP.md`.

La regla es simple:

- `README.md` mantiene la vision y la guia operativa corta.
- `ROADMAP.md` mantiene el estado vivo del proyecto.
- `AGENTS.md` obliga a leer y mantener ambos.

## Requisitos de entorno

- July requiere Python `3.11` o superior.
- En Windows puedes tener varias versiones de Python instaladas en el mismo equipo sin problema.
- Si `python --version` apunta a `3.10` u otra version antigua, usa el launcher de Windows con un Python compatible: `py -3.11 -m july ...` o cualquier `3.11+` disponible, por ejemplo `py -3.13 -m july ...`.
- Los ejemplos de este README usan `python -m july` asumiendo que ya estas dentro de un entorno virtual correcto o que `python` apunta a un runtime `3.11+`.

### Flujo recomendado en Windows

Para evitar mezclar el Python global del equipo con el de July:

```powershell
.\scripts\bootstrap.ps1
.\scripts\july.ps1 stats
```

`bootstrap.ps1` crea `.venv`, actualiza `pip` e instala July en modo editable.  
Si no le pasas una version, intenta usar `3.13`, `3.12` y luego `3.11`.
`july.ps1` ejecuta siempre July con el Python del proyecto.

Accesos directos incluidos:

- `.\scripts\july.ps1 <comando>` para cualquier comando de July.
- `.\scripts\mcp.ps1` para arrancar el servidor MCP.
- `.\scripts\ui.ps1 [--open]` para arrancar el cockpit local de July.
- `.\start-july-mcp.cmd` para arrancar MCP sin recordar comandos de Python o PowerShell.

Si necesitas forzar otra version concreta instalada en tu maquina:

```powershell
.\scripts\bootstrap.ps1 -PythonVersion 3.11
.\scripts\bootstrap.ps1 -PythonVersion 3.13
```

### Flujo en WSL / Linux / macOS

```bash
python3 -m venv .venv
.venv/bin/pip install -e .
./scripts/july.sh stats
```

Accesos directos incluidos:

- `./scripts/july.sh <comando>` para cualquier comando de July.
- `./scripts/mcp.sh` para arrancar el servidor MCP.
- `./scripts/ui.sh [--open]` para arrancar el cockpit local de July.
- `./start-july-mcp.sh` para arrancar MCP directamente.

## Intencion del proyecto

July no debe sentirse como "otra CLI para guardar notas". Debe sentirse como una capa de memoria y orquestacion que acompana el trabajo real dentro de cualquier proyecto conectado.

Objetivo operativo:

- saber en que punto esta un proyecto;
- saber que se ha hecho y que queda por hacer;
- evitar repetir en iteraciones futuras errores, decisiones o analisis ya resueltos;
- conservar contexto util entre conversaciones, herramientas y sesiones.

Experiencia objetivo:

- cuando July se conecta a un proyecto nuevo, debe proponer una revision u onboarding del repositorio;
- durante la iteracion, debe detectar hallazgos utiles, errores resueltos y mejoras de flujo de trabajo;
- cuando algo merece persistir, debe poder preguntarlo de forma natural: "quieres que lo guarde?", "quieres que esto quede como referencia para otro momento?";
- al volver a conversar despues, debe recuperar contexto previo del proyecto sin obligar al usuario a empezar de cero.

Importante: esta es la experiencia objetivo del producto. El codigo actual ya implementa la base de memoria, sesiones, trazabilidad, MCP, un primer cockpit local por proyecto, un wizard inicial con perfilado del tipo de proyecto y sugerencias de skills registradas.

## Que implementa este corte

### Nucleo original (v0.1)

- Captura de entrada libre desde CLI o stdin.
- Clasificacion heuristica de intencion.
- Soporte para inputs sin formulario fijo.
- Almacenamiento local en SQLite.
- FTS5 para buscar inbox y memoria.
- Creacion de tareas y memoria candidata cuando tiene sentido.
- Deteccion de dudas y generacion de preguntas de aclaracion.
- Resolucion de aclaraciones sobre un inbox item existente.
- Promocion de memoria candidata a memoria estable.
- Capa LLM opcional y desacoplada para refinar clasificacion y destilado.
- Primer MCP server por stdio para exponer July a clientes externos.

### Nuevo en v0.2

- Protocolo de sesion completo: `session-start`, `session-summary`, `session-end`, `session-context`.
- Hilos tematicos con `topic_key`: crear temas, enlazar items/memorias/sesiones, consultar contexto por tema.
- Recuperacion proactiva: al capturar un input, July busca automaticamente en memoria y sugiere reutilizar conocimiento previo.
- Extraccion de metadatos de URLs: titulo, descripcion, tipo de contenido. Manejo especial de YouTube (video id, canal, duracion).
- Trazabilidad de modelos: registrar contribuciones de Claude, GPT, Z.AI, Codex, Perplexity, Genspark u otros. Marcar como adoptadas o no.
- Referencias externas: July sugiere consultar skills.sh y agents.md cuando detecta que un input podria beneficiarse de una skill o un patron de agente.
- 17 herramientas MCP expuestas (antes 6).
- 27 comandos CLI (antes 11).

### Nuevo en v0.3

- Primera capa conversacional por proyecto: `project-entry`, `project-onboard`, `project-action`, `conversation-checkpoint`.
- `project_entry` detecta si el proyecto es nuevo, parcial o conocido y devuelve un mensaje tipo wizard con opciones.
- `project_onboard` hace una lectura read-only de README, manifiestos y entrypoints visibles para guardar una primera foto util del repo.
- `project_action` permite ejecutar la respuesta del wizard sin obligar al usuario a memorizar infraestructura.
- `conversation_checkpoint` clasifica un hallazgo como guardable, ambiguo o ignorado y puede persistirlo cuando la senal es clara.
- 21 herramientas MCP expuestas.
- 31 comandos CLI.

### Nuevo en v0.4

- Primer cockpit local por proyecto en `localhost`, pensado como ventana operativa y no como otro chat.
- Registro canonico de proyectos en SQLite para resolver `project_key -> repo_root` y soportar deep links estables.
- `ProjectCockpitService` como capa de lectura y acciones explicitas sobre sesiones, decisiones, hallazgos y pendientes.
- UI web local con `FastAPI + Jinja2 + uvicorn`, renderizado server-side y formularios HTML simples.
- Refinamiento inicial de UX del cockpit para priorizar contexto, timeline, memoria reciente y sesiones antes que la escritura manual.
- Nuevos comandos CLI: `ui` y `ui-link`.
- Nuevo launcher: `scripts/ui.ps1` y `scripts/ui.sh`.
- Nuevo tool MCP: `project_ui_link`.
- 22 herramientas MCP expuestas.
- 33 comandos CLI.

### Nuevo en v0.5

- La base de datos por defecto pasa a ser global por usuario: `~/.july/july.db`.
- El registro canonico de proyectos guarda `project_kind`, `project_tags_json` y `preferences_json`.
- `project_entry` perfila si el repo parece `website`, `web_app`, `mobile_app`, `desktop_app`, `backend`, `automation`, `cli_tool`, `library`, `software`, `knowledge_base` o `unknown`.
- July mantiene preferencias por proyecto para decidir que sugerir: Caveman, Design Extract, CodeBurn, resumen automatico y confirmacion antes de guardar.
- `project-action help` devuelve una ayuda conversacional con lo que July sabe, lo que no sabe y lo que puede hacer.
- El cockpit muestra el tipo de proyecto y ofrece una accion de ayuda.
- Suite de skills globales July preparada en `~/.codex/skills` y `~/.claude/skills` para que Codex y Claude apliquen el ritual de entrada, recuperación, ayuda, guardado, pendientes, mejoras y cierre sin duplicarse en el selector.

### Nuevo en v0.6

- Tabla `project_improvements` para guardar ideas o posibles mejoras por proyecto sin convertirlas todavia en tareas.
- Nuevos comandos CLI: `improvement-add`, `improvements` e `improvement-status`.
- Nuevas herramientas MCP: `project_improvement_add`, `project_improvements` y `project_improvement_status`.
- `project-context`, busqueda y cockpit incluyen mejoras abiertas junto a memoria, sesiones, inbox y pendientes.
- El cockpit permite crear mejoras, priorizarlas y marcarlas como `planned`, `in_progress`, `done` o `dismissed`.
- Pendientes por proyecto expuestos como comandos `pending-add`, `pendings`, `pending-status` y herramientas MCP `project_pending_add`, `project_pendings`, `project_pending_status`.
- 31 herramientas MCP expuestas.
- 41 comandos CLI.
- 14 tablas en la base de datos.

### Nuevo en v0.7

- Tabla `skill_references` para registrar skills locales como referencias reutilizables sin mezclarlas con memoria de proyecto.
- Nuevos comandos CLI: `skill-register`, `skills` y `skill-suggest`.
- Nuevas herramientas MCP: `skill_register`, `skill_references` y `skill_suggest`.
- `proactive_recall` y `project_entry` devuelven `skill_suggestions` cuando el contexto encaja con una skill registrada.
- July puede recordar skills globales y sugerirlas en otros proyectos, por ejemplo `entrevistador-procesos` cuando el usuario quiere crear o automatizar un flujo todavia ambiguo.
- 34 herramientas MCP expuestas.
- 44 comandos CLI.
- 15 tablas en la base de datos.

### Nuevo en v0.8

- Ritual de destilado July a wiki integrado en el producto: tabla `project_distillations`, comandos `distill-candidates` y `distill-record`.
- Nuevas herramientas MCP: `project_distill_candidates` y `project_distillation_record`.
- `session-end` devuelve un semáforo de destilado cuando la sesión pertenece a un proyecto.
- El cockpit muestra aviso cuando un proyecto acumula al menos 5 sesiones cerradas sin destilar o tiene decisiones/hallazgos duraderos candidatos a wiki.
- 36 herramientas MCP expuestas.
- 46 comandos CLI.
- 16 tablas en la base de datos.

### Refactorización técnica iniciada

- La versión instalable del paquete queda alineada con el estado documentado: `0.8.0`.
- GitHub Actions ejecuta la suite de tests de `apps/july` en Python 3.11 para pushes y pull requests que toquen July.
- La infraestructura SQLite empieza a separarse de `july.db`: el esquema vive en `july.storage.schema`, las migraciones explícitas en `july.storage.migrations` y los helpers puros de fechas, arrays JSON y tokens de skills viven en `july.storage.utils`.
- El primer repositorio por dominio es `july.repositories.skill_repository.SkillRepository`, responsable de registrar, listar y sugerir skills.
- `july.repositories.session_repository.SessionRepository` contiene el protocolo de sesiones: inicio, resumen, cierre, contexto y sesión abierta.
- `july.repositories.project_repository.ProjectRepository` contiene el registro canónico de proyectos, contexto agregado por proyecto y totales usados por cockpit, CLI y MCP.
- `july.repositories.task_repository.TaskRepository` contiene mejoras posibles, pendientes y tareas manuales por proyecto.
- `july.repositories.memory_repository.MemoryRepository` contiene inbox, tareas derivadas, memoria candidata/estable, aclaraciones y promoción de memoria.
- `july.repositories.topic_repository.TopicRepository` contiene creación de topic keys, enlaces y contexto agrupado por tema.
- `july.repositories.reference_repository.ReferenceRepository` contiene contribuciones de modelos, metadatos de URLs y referencias externas.
- `july.repositories.search_repository.SearchRepository` contiene búsqueda FTS/fallback y recuperación proactiva con sugerencias de skills.
- `july.analyzer` queda como fachada pública y delega modelos, descubrimiento, arquitectura, imports, smells y recomendaciones en `july.analysis.*`.
- `july.project_conversation` conserva la fachada de servicio y delega helpers puros en `july.project_surface`, `july.project_messages`, `july.project_checkpoints` y `july.project_text`.
- `july.project_conversation` también delega onboarding/acciones en `july.project_lifecycle` y checkpoints/mejoras/pendientes en `july.project_memory_actions`.
- `july.cockpit` conserva `ProjectCockpitService` y delega builders de sugerencias/timeline en `july.cockpit_builders`.
- `july.cli` queda como bootstrap: crea contexto, mantiene `build_parser` vía `july.cli_parser` y delega dispatch en familias bajo `july.cli_handlers`.
- `july.mcp` queda como servidor stdio/bootstrap: las familias de schemas y handlers MCP viven bajo `july.mcp_tools` y los tipos/coerciones comunes en `july.mcp_utils`.
- `july.db.JulyDatabase` sigue siendo la fachada pública compatible para CLI, MCP, cockpit y tests.

## Modelo operativo

Pipeline actual:

`input libre -> extraer urls/rutas/proyecto -> clasificar -> recall proactivo -> sugerir skills registradas -> guardar inbox -> crear tarea/memoria candidata/mejora/pendiente -> fetch URL metadata -> sugerir referencias externas -> recuperar`

Flujo actual sobre ese pipeline:

`proyecto nuevo -> project_entry -> perfilar tipo/preferencias -> pedir permiso -> project_onboard -> iterar -> conversation_checkpoint/improvement-add/pending-add -> session-summary -> recuperar contexto`

Flujo local del cockpit:

`abrir repo o project_key -> /projects/{project_key} -> revisar proyecto -> registrar decision/hallazgo/mejora/pendiente -> organizar pendientes -> resumir/cerrar sesion`

Flujo objetivo ampliado:

`proyecto nuevo -> detectar contexto -> ofrecer onboarding/revision -> iterar -> registrar avances y decisiones -> resumir estado -> recuperar contexto en la siguiente conversacion`

July mantiene una sola memoria global. La separacion por web, app o software se hace con metadatos del proyecto, no con bases de datos distintas, para conservar busqueda cruzada entre proyectos.

Principio de UX:

- MCP y CLI son infraestructura;
- la experiencia deseada para el usuario es conversacional;
- el agente debe usar July por detras para recordar, sugerir y consolidar, no obligar al usuario a memorizar comandos.

Tipos de intencion iniciales:

- `repository_onboarding`
- `resource_watch_later`
- `resource_apply_to_project`
- `memory_query`
- `repository_audit_with_memory`
- `external_analysis_import`
- `architecture_collaboration`
- `general_note`

## Uso rapido de la infraestructura actual

Los comandos de abajo son utiles para probar July, depurarlo o usarlo manualmente. No representan la UX final deseada del producto. La UX objetivo es que el agente haga este trabajo por detras y lo exponga en forma de preguntas y sugerencias naturales.

### 1. Capturar una entrada libre

```powershell
.\scripts\july.ps1 capture "Quiero que me recuerdes ver este link: https://youtu.be/91BGGKlQrho"
```

```powershell
.\scripts\july.ps1 capture "He visto un curso que quiero aplicar en Lucy3000 = https://www.youtube.com/live/V-eiE0M-mWM" --fetch-urls
```

```powershell
.\scripts\july.ps1 capture "Accede a C:\Users\sergi\Desktop\Aplicaciones\Vocabulario, comprueba los accesos" --model-name claude
```

### 2. Ver el inbox

```powershell
.\scripts\july.ps1 inbox
```

### 3. Resolver una aclaracion

```powershell
.\scripts\july.ps1 clarify 3 "Quiero una auditoria tecnica completa"
```

### 4. Ver tareas pendientes

```powershell
.\scripts\july.ps1 tasks
```

### 5. Ver memoria candidata o lista

```powershell
.\scripts\july.ps1 memory
```

### 6. Promover una memoria candidata

```powershell
.\scripts\july.ps1 promote-memory 1
```

### 7. Ver contexto agrupado por proyecto

```powershell
.\scripts\july.ps1 project-context Vocabulario
```

### 8. Buscar contexto

```powershell
.\scripts\july.ps1 search skill
.\scripts\july.ps1 search MCP
.\scripts\july.ps1 search Lucy3000
```

### 9. Probar una clasificacion sin guardar

```powershell
.\scripts\july.ps1 capture "Quiero montar JWT en Vocabulario" --dry-run
```

### 10. Protocolo de sesion

```powershell
# Iniciar sesion
.\scripts\july.ps1 session-start "ses-001" --project Lucy3000 --agent claude --goal "Implementar JWT"

# Guardar resumen antes de cerrar
.\scripts\july.ps1 session-summary "ses-001" "Implementamos JWT con refresh tokens" --discoveries "httpOnly cookie obligatoria" --next-steps "Proteger rutas privadas"

# Cerrar sesion
.\scripts\july.ps1 session-end "ses-001"

# Recuperar contexto de sesiones recientes
.\scripts\july.ps1 session-context --project Lucy3000

# Listar sesiones
.\scripts\july.ps1 sessions
```

### 11. Hilos tematicos (topic keys)

```powershell
# Crear un tema
.\scripts\july.ps1 topic-create "auth/jwt-flow" "Autenticacion JWT" --domain Programacion --description "Todo sobre JWT y refresh tokens"

# Enlazar items al tema
.\scripts\july.ps1 topic-link "auth/jwt-flow" --memory-item-id 1
.\scripts\july.ps1 topic-link "auth/jwt-flow" --session-id 1

# Ver todo lo vinculado a un tema
.\scripts\july.ps1 topic-context "auth/jwt-flow"

# Listar temas
.\scripts\july.ps1 topics
```

### 12. Trazabilidad de modelos

```powershell
# Registrar una contribucion
.\scripts\july.ps1 model-contribution "claude" "architecture" "Propuesta JWT" "Usar refresh tokens en httpOnly cookies" --project Vocabulario

# Listar contribuciones
.\scripts\july.ps1 model-contributions --project Vocabulario

# Marcar como adoptada
.\scripts\july.ps1 adopt-contribution 1 --notes "Adoptada por experiencia previa en Lucy3000"
```

### 13. Fetch de URLs

```powershell
.\scripts\july.ps1 fetch-url "https://github.com/Gentleman-Programming/engram"
```

### 14. Referencias externas

```powershell
# Consultar una fuente de referencia conocida
.\scripts\july.ps1 fetch-reference skills.sh
.\scripts\july.ps1 fetch-reference agents.md

# Ver referencias almacenadas
.\scripts\july.ps1 external-references
```

### 15. Lanzar el servidor MCP

**Windows (PowerShell):**

```powershell
.\scripts\mcp.ps1
```

O directamente:

```powershell
.\start-july-mcp.cmd
```

**WSL / Linux / macOS:**

```bash
./scripts/mcp.sh
```

O directamente:

```bash
./start-july-mcp.sh
```

### 16. Wizard conversacional por proyecto

```powershell
# Detectar estado del proyecto y devolver la primera pregunta
.\scripts\july.ps1 project-entry --repo-path "C:\Users\sergi\Desktop\Aplicaciones\Dashboard_AV"

# Aceptar el analisis read-only inicial
.\scripts\july.ps1 project-action analyze_now --repo-path "C:\Users\sergi\Desktop\Aplicaciones\Dashboard_AV" --agent codex

# Pedir ayuda sobre lo que July sabe y no sabe del proyecto
.\scripts\july.ps1 project-action help --repo-path "C:\Users\sergi\Desktop\Aplicaciones\Dashboard_AV"

# Guardar un hallazgo reutilizable durante la iteracion
.\scripts\july.ps1 conversation-checkpoint "Decision: usar ExcelJS porque evita automatizaciones fragiles con COM." --repo-path "C:\Users\sergi\Desktop\Aplicaciones\Dashboard_AV" --persist
```

Notas operativas:

- `project-entry` debe ser el primer paso cuando July entra en un repo nuevo o dudoso.
- `project-onboard` y `project-action analyze_now` leen el repo en modo solo lectura y guardan la primera foto dentro de la BD de July.
- `project-action help` explica que sabe July, que no sabe y que puede hacer en ese proyecto.
- `conversation-checkpoint` no debe usarse para volcar ruido; sirve para decisiones, errores resueltos y mejoras de flujo.

### 17. Mejoras posibles por proyecto

```powershell
# Guardar una idea de mejora ligada al proyecto detectado por repo_path
.\scripts\july.ps1 improvement-add "Incluir filtro de disponibilidad por franja horaria" --repo-path "C:\Users\sergi\Desktop\Aplicaciones\Indalo_padel"

# Ver mejoras abiertas de un proyecto
.\scripts\july.ps1 improvements --project-key indalo-padel

# Marcar una mejora como planificada, en progreso, hecha o descartada
.\scripts\july.ps1 improvement-status 12 planned --project-key indalo-padel
```

Uso conversacional esperado:

> Accede a July e incluye como posible mejora: permitir que el usuario filtre pistas por disponibilidad real.

July debe resolver el proyecto activo, guardar la mejora como `open` y recuperarla mas tarde cuando el usuario pregunte que mejoras quedan por implementar.

### 18. Pendientes por proyecto

```powershell
# Guardar un pendiente ligado al proyecto detectado por repo_path
.\scripts\july.ps1 pending-add "Revisar FCM en iOS con app en foreground" --repo-path "C:\Users\sergi\Desktop\Aplicaciones\Indalo_padel"

# Ver pendientes abiertos de un proyecto
.\scripts\july.ps1 pendings --project-key indalo-padel

# Marcar un pendiente como en curso o terminado
.\scripts\july.ps1 pending-status 18 in_progress --project-key indalo-padel
.\scripts\july.ps1 pending-status 18 done --project-key indalo-padel
```

Uso conversacional esperado:

> Accede a July e incluye como pendiente: revisar FCM en iOS con app en foreground.

July debe resolver el proyecto activo, guardar el pendiente como `pending` y recuperarlo mas tarde cuando el usuario pregunte que queda por hacer. Cuando se complete, debe marcarse como `done`.

### 19. Skills registradas como referencias

```powershell
# Registrar una skill local empaquetada
.\scripts\july.ps1 skill-register "C:\Users\sergi\Documents\Skills\planificador-procesos.skill" --domain skills --domain procesos --domain automatizacion --domain workflow

# Pedir sugerencias contra un objetivo o contexto de trabajo
.\scripts\july.ps1 skill-suggest "Quiero crear una automatizacion pero no tengo claro el proceso" --project-key indalo-padel

# Ver skills registradas y comandos locales de memoria
.\scripts\july.ps1 skills

# Ver solo skills reutilizables sugeribles
.\scripts\july.ps1 skills --registered-only
```

Uso conversacional esperado:

> July, voy a crear una automatizacion compleja, pero todavia no tengo claro el proceso.

July debe poder responder algo como: "Oye Sergio, para esto conviene usar `entrevistador-procesos` antes de construir, porque el flujo todavia no esta cerrado."

### 20. Cockpit local por proyecto

```powershell
# Arrancar la UI local
.\scripts\ui.ps1 --open

# Construir un deep link por project_key
.\scripts\july.ps1 ui-link --project-key dashboard-av

# Registrar o refrescar un proyecto al construir el link
.\scripts\july.ps1 ui-link --project-key dashboard-av --repo-path "C:\Users\sergi\Desktop\Aplicaciones\Dashboard_AV"
```

La UI local expone una pagina por proyecto con:

- proyecto activo, `project_key` y `repo_root`;
- tipo de proyecto detectado;
- estado `new`, `partial` o `known`;
- consola de contexto con timeline reciente de memoria, sesiones, inbox y pendientes;
- sesion activa o ultima sesion;
- memoria reciente y hallazgos recientes;
- pendientes manuales;
- mejoras posibles abiertas;
- aviso de destilado July a wiki cuando el proyecto acumula sesiones o hallazgos duraderos;
- sugerencias read-only;
- acciones explicitas plegables para revisar proyecto, registrar decision, guardar hallazgo, guardar mejora, organizar pendientes y preparar la siguiente sesion.

Variables de configuracion UI:

- `JULY_UI_HOST`
- `JULY_UI_PORT`
- `JULY_UI_BASE_URL`

Herramientas MCP expuestas actualmente (`36`):

- `capture_input` (con proactive recall, fetch URLs, model traceability)
- `search_context`
- `project_context`
- `project_improvement_add`
- `project_improvements`
- `project_improvement_status`
- `project_pending_add`
- `project_pendings`
- `project_pending_status`
- `project_distill_candidates`
- `project_distillation_record`
- `project_entry`
- `project_onboard`
- `project_action`
- `project_ui_link`
- `list_inbox`
- `clarify_input`
- `promote_memory`
- `session_start`
- `session_summary`
- `session_end`
- `session_context`
- `topic_create`
- `topic_link`
- `topic_context`
- `save_model_contribution`
- `fetch_url`
- `fetch_reference`
- `skill_register`
- `skill_references`
- `skill_suggest`
- `proactive_recall`
- `conversation_checkpoint`
- `architect_insights`
- `developer_level`
- `plug_project`

Ejemplo de configuracion MCP por stdio (Windows):

```json
{
  "mcpServers": {
    "july": {
      "command": "cmd",
      "args": ["/c", "C:\\Users\\sergi\\Desktop\\Aplicaciones\\July_unificada\\apps\\july\\start-july-mcp.cmd"],
      "cwd": "C:\\Users\\sergi\\Desktop\\Aplicaciones\\July_unificada\\apps\\july"
    }
  }
}
```

Ejemplo de configuracion MCP por stdio (WSL / Linux / macOS):

```json
{
  "mcpServers": {
    "july": {
      "command": "bash",
      "args": ["/ruta/a/July_unificada/apps/july/start-july-mcp.sh"],
      "cwd": "/ruta/a/July_unificada/apps/july"
    }
  }
}
```

## Donde guarda los datos

Por defecto la base vive en:

`~/.july/july.db`

Ese default es intencionado: July debe actuar como una memoria unificada entre proyectos. Si se usara `./data/july.db` en cada repo, cada proyecto acabaria con una memoria aislada.

Se puede cambiar con:

`JULY_DB_PATH`

July carga automaticamente un archivo `.env` en la raiz del proyecto si existe, asi que `JULY_DB_PATH` tambien puede vivir ahi.

## Esquema de base de datos

Tablas principales:

| Tabla | Funcion |
|---|---|
| `inbox_items` | Entradas brutas capturadas |
| `tasks` | Tareas derivadas de inputs |
| `memory_items` | Memoria candidata y estable |
| `artifacts` | URLs y rutas detectadas |
| `project_links` | Relaciones entre items y proyectos |
| `clarification_events` | Historial de aclaraciones |
| `sessions` | Sesiones de trabajo con inicio, resumen y cierre |
| `topic_keys` | Temas estables para agrupar conocimiento |
| `topic_links` | Enlaces entre temas y items/memorias/sesiones |
| `model_contributions` | Contribuciones trazables de modelos IA |
| `url_metadata` | Metadatos extraidos de URLs (titulo, descripcion, YouTube) |
| `external_references` | Referencias a fuentes externas (skills.sh, agents.md) |
| `skill_references` | Skills locales registradas para sugerencias proactivas |
| `project_distillations` | Cortes de destilado July a wiki por proyecto |
| `projects` | Registro canonico de proyectos para cockpit, deep links, tipo de proyecto, tags y preferencias |

Indices FTS5: `inbox_items_fts`, `memory_items_fts`.

## Capa LLM opcional

July puede pedir ayuda a un proveedor LLM para:

- refinar clasificaciones ambiguas;
- mejorar resumenes;
- destilar memoria candidata.

OpenAI es la configuracion principal documentada ahora mismo:

```powershell
$env:JULY_LLM_PROVIDER="openai_compatible"
$env:JULY_LLM_MODEL="gpt-4.1-mini"
$env:JULY_LLM_API_KEY="tu-api-key"
$env:JULY_LLM_BASE_URL="https://api.openai.com/v1"
```

Variables soportadas:

- `JULY_LLM_PROVIDER`
- `JULY_LLM_MODEL`
- `JULY_LLM_API_KEY`
- `JULY_LLM_BASE_URL`
- `JULY_LLM_TIMEOUT`

Estas variables pueden definirse en `.env` o en el entorno del sistema.

July mantiene una arquitectura compatible con otros proveedores `OpenAI-compatible`. Z.ai sigue siendo una alternativa compatible, pero ya no es el ejemplo principal del proyecto.

## Mesa redonda de modelos

Uno de los puntos fuertes de July es que todas las opiniones cuentan. Claude, Codex, Z.ai, Perplexity, Genspark y otros modelos pueden aportar ideas validas.

La intencion no es seguir ciegamente a un unico modelo, sino montar una mesa redonda:

- cada modelo puede aportar un planteamiento;
- cada aportacion se registra con `model-contribution` y queda trazable;
- las aportaciones pueden compararse con `model-contributions`;
- la decision final se marca como adoptada con `adopt-contribution`;
- las no adoptadas quedan como registro historico, no se borran.

July no esta pensado para una unica voz. Esta pensado para aprovechar el contraste entre varias IAs y convertirlo en conocimiento util y trazable.

## Recuperacion proactiva

Cada vez que se captura una nueva entrada, July busca automaticamente en su memoria y sesiones previas:

- Si encuentra memorias globales reutilizables, sugiere reutilizarlas.
- Si encuentra memorias de otros proyectos con contenido similar, avisa con `cross_project`.
- Si hay sesiones recientes del mismo proyecto, las incluye como contexto.

Esto convierte a July en un sistema que **recuerda por ti y te avisa cuando algo es relevante**, no solo un almacen pasivo.

## Modo de trabajo esperado en un proyecto

El contrato operativo exacto vive en `PROJECT_PROTOCOL.md`.

Resumen corto del comportamiento esperado:

1. Detectar primero si el proyecto es nuevo o ya conocido usando `project-context`, `session-context` y la documentacion real del repo.
2. Si es nuevo, proponer onboarding o revision y guardar una primera foto util del proyecto.
3. Si es conocido, recuperar contexto antes de pedir al usuario que repita informacion y evitar rehacer onboarding sin necesidad.
4. Durante la iteracion, guardar solo conocimiento durable y reutilizable; si hay ambiguedad, preguntar.
5. Al cerrar, dejar una sesion resumida con hecho, pendiente y siguiente paso.
6. Fase 1 significa que el agente lee el repo y July actua como memoria; Fase 2, si hace falta, permitira lectura controlada y read-only por parte de July.

Eso permite que July sirva como memoria anti-regresion: no solo guarda, sino que reduce trabajo repetido y ayuda a retomar donde se dejo el proyecto.

## Referencias externas como punto de apoyo

July puede sugerir consultar fuentes externas cuando detecta que un input se beneficiaria de ellas:

- **skills.sh**: Cuando el input implica crear patrones reutilizables, plantillas, workflows o scaffolding.
- **agents.md**: Cuando el input implica crear agentes, sub-agentes, orquestacion o automatizacion.

Estas sugerencias son puntos de referencia. July toma la idea, la revisa, y crea su propia implementacion. No depende de ellas ni las copia literalmente.

## Skills registradas como punto de apoyo

July tambien puede registrar skills locales existentes para sugerirlas mas adelante. Estas referencias no ejecutan nada por si solas: solo permiten que `proactive_recall`, `project_entry` o `skill-suggest` recuerden que una herramienta puede ayudar.

El comando `skills` separa dos categorias:

- **Skills de trabajo reutilizable**: referencias registradas en `skill_references`, sugeribles por `skill-suggest` entre proyectos.
- **Comandos July / memoria operativa**: wrappers locales de `skills/` como `july`, `july-inicio`, `mejoras` o `pendientes`. Se listan para visibilidad, pero no contaminan el ranking de `skill-suggest`.

Ejemplos ya validados:

- `planificador-procesos.skill` se registra internamente como `entrevistador-procesos` y puede sugerirse cuando un proyecto o conversacion implique crear, automatizar, documentar o definir un proceso ambiguo.
- `optimizador-prompts.skill` se sugiere para ordenar ideas o convertir instrucciones incompletas en prompts claros.
- `presentaciones-visuales.skill` se sugiere para transformar contenido en slides, decks o presentaciones HTML visuales.
- `superpowers.skill` se sugiere cuando una tarea compleja requiere entender, planificar, definir riesgos y validar antes de construir.

Uso conversacional esperado:

- "Oye July, quiero hacer X, tenemos alguna skill que me pueda ayudar?"
- "Oye July, cual era la skill que hacia Y?"

## Como interpretar este MVP

- No todo lo que entra se convierte en memoria.
- Todo lo que entra puede quedar en inbox.
- Los links pendientes suelen generar tarea, no memoria estable.
- Las revisiones de repo, arquitectura o planteamientos externos pueden generar memoria candidata o util directamente.
- Si la clasificacion no es suficientemente segura, July marca la entrada como `needs_clarification`.
- Una aclaracion actualiza el mismo `inbox_item`; no crea otro distinto.
- Al capturar, July busca proactivamente en memoria y sugiere reutilizar conocimiento previo.
- Las sesiones permiten consolidar el conocimiento de un bloque de trabajo.
- Los topic keys permiten agrupar conocimiento disperso bajo un mismo hilo.
- El protocolo por proyecto ya esta definido a nivel documental en `PROJECT_PROTOCOL.md`.
- El estado actual ya automatiza el primer corte del wizard conversacional por proyecto y un primer cockpit local, pero todavia quedan refinamientos de continuidad, staleness y sugerencias cross-project mas ricas.

## Contrato publico del proyecto

- `README.md` es la vision y la guia operativa corta.
- `ROADMAP.md` es el estado vivo y la direccion del proyecto.
- `AGENTS.md` es la instruccion obligatoria para cualquier agente o CLI que contribuya.
- `PROJECT_PROTOCOL.md` fija el contrato operativo exacto de July dentro de proyectos conectados.

Estos cuatro archivos deben mantenerse alineados.
