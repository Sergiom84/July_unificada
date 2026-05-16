# Plan de mejora y refactorización para `July_unificada`

Fecha: 2026-05-16  
Objetivo: ordenar July antes de seguir añadiendo funcionalidades grandes.

## 0. Regla principal

No intentes hacerlo todo en una sola tanda.

La prioridad es esta:

1. Alinear versión y documentación.
2. Añadir verificación automática.
3. Modularizar sin cambiar comportamiento.
4. Mantener CLI, MCP y comandos actuales funcionando.
5. Solo después, añadir nuevas funciones.

Durante todo el proceso, después de cada bloque pequeño ejecuta tests. Si algo falla, arregla antes de seguir.

---

## 1. Preparación inicial

### 1.1 Crear rama de trabajo

Desde la raíz del repo:

```bash
git checkout main
git pull
git checkout -b refactor/july-core
```

### 1.2 Ejecutar tests actuales antes de tocar nada

```bash
cd apps/july
python -m pip install -e .
python -m unittest discover -s tests
```

En Windows, si `python` no apunta a Python 3.11+:

```powershell
cd apps/july
py -3.11 -m pip install -e .
py -3.11 -m unittest discover -s tests
```

### 1.3 Resultado esperado

- Los tests pasan.
- Sabes cuál es el estado inicial.
- Si algo falla ya desde el inicio, no refactorices todavía: primero arregla el test o documenta el fallo.

---

## 2. Alinear versión del paquete

### Problema

La documentación habla de una versión más avanzada que la versión declarada en el paquete. Esto genera confusión entre README, CLI, MCP y paquete instalable.

### Archivos a revisar

```text
apps/july/pyproject.toml
apps/july/july/__init__.py
apps/july/README.md
apps/july/ROADMAP.md
```

### Qué hacer

Elige una versión actual real. Por ejemplo:

```text
0.7.0
```

Después actualiza:

```toml
# apps/july/pyproject.toml
[project]
version = "0.7.0"
```

```python
# apps/july/july/__init__.py
"""July package."""

__version__ = "0.7.0"
```

### Validación

```bash
cd apps/july
python -c "import july; print(july.__version__)"
python -m unittest discover -s tests
```

### Criterio de finalización

- `pyproject.toml` y `july/__init__.py` muestran la misma versión.
- El README no contradice esa versión.
- Los tests siguen pasando.

---

## 3. Añadir CI mínima con GitHub Actions

### Objetivo

Que cada push o pull request ejecute los tests automáticamente.

### Crear archivo

```text
.github/workflows/july-tests.yml
```

### Contenido recomendado

```yaml
name: July tests

on:
  push:
    paths:
      - "apps/july/**"
      - ".github/workflows/july-tests.yml"
  pull_request:
    paths:
      - "apps/july/**"
      - ".github/workflows/july-tests.yml"

jobs:
  test:
    runs-on: ubuntu-latest

    defaults:
      run:
        working-directory: apps/july

    steps:
      - name: Checkout
        uses: actions/checkout@v6

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install package
        run: |
          python -m pip install --upgrade pip
          python -m pip install -e .

      - name: Run tests
        run: python -m unittest discover -s tests
```

### Validación

```bash
git add .github/workflows/july-tests.yml
git commit -m "ci: add July test workflow"
git push -u origin refactor/july-core
```

Después revisa en GitHub que el workflow pasa.

### Criterio de finalización

- Existe `.github/workflows/july-tests.yml`.
- GitHub Actions ejecuta los tests.
- El job pasa en Python 3.11.

---

## 4. Refactorizar `db.py` sin romper compatibilidad

### Problema

`apps/july/july/db.py` hace demasiadas cosas:

- conexión SQLite;
- creación de esquema;
- migraciones;
- inbox;
- memoria;
- tareas;
- mejoras;
- proyectos;
- sesiones;
- topics;
- contribuciones de modelos;
- URLs;
- referencias externas;
- skills;
- búsqueda;
- perfil del desarrollador.

No hay que reescribirlo de golpe. Hay que convertirlo poco a poco en una fachada que delega.

### Regla importante

No crees una carpeta llamada:

```text
apps/july/july/db/
```

porque ya existe:

```text
apps/july/july/db.py
```

Para evitar conflictos, usa carpetas como:

```text
apps/july/july/storage/
apps/july/july/repositories/
```

---

## 5. Extraer infraestructura de base de datos

### Crear estructura

```text
apps/july/july/storage/
  __init__.py
  schema.py
  utils.py
```

### Mover a `storage/schema.py`

Desde `db.py`, mueve:

```python
SCHEMA_SQL = """..."""
```

a:

```python
# apps/july/july/storage/schema.py

SCHEMA_SQL = """..."""
```

### Mover a `storage/utils.py`

Mueve funciones auxiliares como:

```python
utc_now()
normalize_json_array()
parse_json_array()
skill_reference_tokens()
```

a:

```python
# apps/july/july/storage/utils.py
```

### Ajustar `db.py`

En `db.py` importa:

```python
from july.storage.schema import SCHEMA_SQL
from july.storage.utils import (
    normalize_json_array,
    parse_json_array,
    skill_reference_tokens,
    utc_now,
)
```

### Validación

```bash
cd apps/july
python -m unittest discover -s tests
```

### Commit

```bash
git add apps/july/july/db.py apps/july/july/storage
git commit -m "refactor: extract database schema utilities"
```

### Criterio de finalización

- `db.py` sigue importándose con `from july.db import JulyDatabase`.
- No cambia ningún comando.
- Los tests pasan.

---

## 6. Crear repositorios por dominio

### Objetivo

Que `JulyDatabase` siga existiendo, pero delegue.

Crear:

```text
apps/july/july/repositories/
  __init__.py
  skill_repository.py
  project_repository.py
  session_repository.py
  task_repository.py
  memory_repository.py
  topic_repository.py
  reference_repository.py
  search_repository.py
  developer_repository.py
```

No hace falta crear todos de golpe. Hazlo en este orden.

---

## 7. Extraer primero `SkillRepository`

### Por qué primero

Es una zona relativamente aislada y reciente. Reduce riesgo.

### Mover desde `db.py`

Métodos relacionados:

```python
upsert_skill_reference()
list_skill_references()
suggest_skill_references()
```

y helpers directos relacionados con skills.

### Crear archivo

```python
# apps/july/july/repositories/skill_repository.py

from __future__ import annotations

import json
import sqlite3

from july.storage.utils import (
    normalize_json_array,
    parse_json_array,
    skill_reference_tokens,
    utc_now,
)

SKILL_REFERENCE_STATUSES = {"active", "inactive"}

class SkillRepository:
    def __init__(self, connection_factory):
        self.connection = connection_factory

    def upsert_skill_reference(...):
        ...

    def list_skill_references(...):
        ...

    def suggest_skill_references(...):
        ...
```

### Mantener compatibilidad en `JulyDatabase`

En `db.py`:

```python
from july.repositories.skill_repository import SkillRepository

class JulyDatabase:
    def __init__(self, settings):
        self.settings = settings
        self.settings.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self.skills = SkillRepository(self.connection)

    def upsert_skill_reference(self, *args, **kwargs):
        return self.skills.upsert_skill_reference(*args, **kwargs)

    def list_skill_references(self, *args, **kwargs):
        return self.skills.list_skill_references(*args, **kwargs)

    def suggest_skill_references(self, *args, **kwargs):
        return self.skills.suggest_skill_references(*args, **kwargs)
```

### Validación

```bash
cd apps/july
python -m unittest discover -s tests
```

Comprueba especialmente tests de:

- `skill-register`;
- `skills`;
- `skill-suggest`;
- `proactive_recall`;
- MCP `skill_references`.

### Commit

```bash
git add apps/july/july/db.py apps/july/july/repositories/skill_repository.py
git commit -m "refactor: extract skill repository"
```

---

## 8. Extraer `SessionRepository`

### Mover desde `db.py`

Métodos:

```python
session_start()
session_summary()
session_end()
session_context()
get_open_session()
list_sessions()
```

### Crear

```text
apps/july/july/repositories/session_repository.py
```

### Mantener fachada en `JulyDatabase`

```python
self.sessions = SessionRepository(self.connection)

def session_start(self, *args, **kwargs):
    return self.sessions.session_start(*args, **kwargs)
```

Haz lo mismo con los demás métodos.

### Validación

```bash
cd apps/july
python -m unittest discover -s tests
```

### Commit

```bash
git add apps/july/july/db.py apps/july/july/repositories/session_repository.py
git commit -m "refactor: extract session repository"
```

---

## 9. Extraer `ProjectRepository`

### Mover desde `db.py`

Métodos:

```python
upsert_project()
touch_project()
get_project()
list_projects()
get_project_totals()
project_context()
```

### Crear

```text
apps/july/july/repositories/project_repository.py
```

### Cuidado

`project_context()` mezcla inbox, tasks, memory e improvements. Puedes hacer una de estas dos cosas:

### Opción A, recomendada al principio

Mover `project_context()` entero a `ProjectRepository`, aunque consulte varias tablas.

### Opción B, más limpia pero posterior

Dividirlo en un `ProjectContextService`.

No hagas la opción B todavía si quieres avanzar sin romper.

### Validación

```bash
cd apps/july
python -m unittest discover -s tests
```

### Commit

```bash
git add apps/july/july/db.py apps/july/july/repositories/project_repository.py
git commit -m "refactor: extract project repository"
```

---

## 10. Extraer tareas, pendientes y mejoras

### Crear

```text
apps/july/july/repositories/task_repository.py
```

### Mover

```python
create_project_improvement()
list_project_improvements()
update_project_improvement_status()
create_manual_task()
list_project_tasks()
update_task_status()
```

### Mantener nombres actuales

Aunque internamente lo llames `TaskRepository`, no cambies todavía nombres públicos como:

```python
database.create_project_improvement()
database.list_project_improvements()
```

### Validación

```bash
cd apps/july
python -m unittest discover -s tests
```

### Commit

```bash
git add apps/july/july/db.py apps/july/july/repositories/task_repository.py
git commit -m "refactor: extract task and improvement repository"
```

---

## 11. Extraer memoria e inbox

### Crear

```text
apps/july/july/repositories/memory_repository.py
```

### Mover

```python
capture()
resolve_clarification()
promote_memory()
_insert_task()
_insert_memory()
_insert_artifacts()
_insert_project_links()
_delete_derived_records()
list_inbox()
list_tasks()
list_memory()
get_record()
```

### Cuidado

Esta parte tiene más riesgo porque `capture()` crea registros derivados. Hazlo en dos pasos:

### Paso 11.1

Mover solo listados y lectura:

```python
list_inbox()
list_tasks()
list_memory()
get_record()
```

Ejecuta tests y commit.

### Paso 11.2

Mover mutaciones:

```python
capture()
resolve_clarification()
promote_memory()
```

Ejecuta tests y commit.

### Commits sugeridos

```bash
git commit -m "refactor: extract memory read repository"
git commit -m "refactor: extract memory capture repository"
```

---

## 12. Extraer topics

### Crear

```text
apps/july/july/repositories/topic_repository.py
```

### Mover

```python
create_topic()
link_to_topic()
topic_context()
list_topics()
```

### Validación

```bash
cd apps/july
python -m unittest discover -s tests
```

### Commit

```bash
git add apps/july/july/db.py apps/july/july/repositories/topic_repository.py
git commit -m "refactor: extract topic repository"
```

---

## 13. Extraer referencias externas, URLs y contribuciones

### Crear

```text
apps/july/july/repositories/reference_repository.py
```

### Mover

```python
save_model_contribution()
list_model_contributions()
adopt_contribution()
save_url_metadata()
get_url_metadata()
save_external_reference()
list_external_references()
```

### Validación

```bash
cd apps/july
python -m unittest discover -s tests
```

### Commit

```bash
git add apps/july/july/db.py apps/july/july/repositories/reference_repository.py
git commit -m "refactor: extract reference repository"
```

---

## 14. Extraer búsqueda

### Crear

```text
apps/july/july/repositories/search_repository.py
```

### Mover

```python
search()
proactive_recall()
```

Si `proactive_recall()` depende de skills, memoria o sesiones, puedes inyectar los repositorios necesarios o mantenerlo temporalmente en `JulyDatabase`.

### Recomendación

Primero mueve solo:

```python
search()
```

Luego mueve `proactive_recall()` cuando el resto esté estable.

### Validación

```bash
cd apps/july
python -m unittest discover -s tests
```

---

## 15. Añadir migraciones simples

### Problema

El esquema SQLite ya es grande. Seguir añadiendo `ALTER TABLE` dentro de `_migrate_legacy_schema()` se volverá difícil.

### No hagas todavía una migración completa a SQLAlchemy

July usa SQLite directo. Mantén eso.

### Crear tabla de migraciones

En `SCHEMA_SQL` añade:

```sql
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    applied_at TEXT NOT NULL
);
```

### Crear módulo

```text
apps/july/july/storage/migrations.py
```

### Idea mínima

```python
MIGRATIONS = [
    (1, "add_project_profile_columns", migrate_001),
    (2, "add_skill_references", migrate_002),
]

def apply_migrations(conn):
    ensure_migrations_table(conn)
    applied = get_applied_versions(conn)
    for version, name, migration in MIGRATIONS:
        if version not in applied:
            migration(conn)
            mark_applied(conn, version, name)
```

### Objetivo

Que futuras alteraciones vivan como migraciones explícitas, no como lógica dispersa.

### Validación

Crear un test con una base antigua mínima:

```python
def test_migrations_apply_to_legacy_database(self):
    ...
```

### Commit

```bash
git add apps/july/july/storage/migrations.py apps/july/tests
git commit -m "refactor: add explicit schema migrations"
```

---

## 16. Refactorizar `project_conversation.py`

### Problema

Este archivo mezcla:

- detección de repo;
- project key;
- lectura de superficie;
- inferencia de perfil;
- mensajes conversacionales;
- onboarding;
- checkpoints;
- mejoras;
- pendientes.

### Crear estructura

```text
apps/july/july/project/
  __init__.py
  identity.py
  surface.py
  profile.py
  messages.py
  onboarding.py
  checkpoints.py
```

### Orden recomendado

#### 16.1 Extraer identidad

Mover:

```python
detect_repo_root()
derive_project_key()
resolve_project_identity()
```

a:

```text
apps/july/july/project/identity.py
```

Validar:

```bash
python -m unittest discover -s tests
```

Commit:

```bash
git commit -m "refactor: extract project identity helpers"
```

#### 16.2 Extraer superficie

Mover:

```python
RepositorySurface
inspect_repository_surface()
analyze_repository()
read_limited_text()
extract_package_commands()
infer_default_commands()
detect_integrations()
extract_objective()
build_open_questions()
```

a:

```text
apps/july/july/project/surface.py
```

Commit:

```bash
git commit -m "refactor: extract project surface analysis"
```

#### 16.3 Extraer perfil

Mover:

```python
ProjectProfile
infer_project_profile()
infer_project_kind()
infer_project_tags()
default_preferences_for_kind()
```

a:

```text
apps/july/july/project/profile.py
```

Commit:

```bash
git commit -m "refactor: extract project profile inference"
```

#### 16.4 Extraer mensajes

Mover:

```python
assess_project_state()
build_context_summary()
build_recall_query()
build_entry_message()
build_permission_request()
recommended_action_for_state()
build_entry_options()
build_project_help()
build_copilot_hint()
```

a:

```text
apps/july/july/project/messages.py
```

Commit:

```bash
git commit -m "refactor: extract project conversation messages"
```

#### 16.5 Extraer checkpoints

Mover:

```python
classify_checkpoint()
build_checkpoint_title()
build_improvement_title()
build_pending_title()
summarize_text()
```

y lógica relacionada a:

```text
apps/july/july/project/checkpoints.py
```

Commit:

```bash
git commit -m "refactor: extract project checkpoints"
```

### Criterio de finalización

- `ProjectConversationService` sigue existiendo.
- Los métodos públicos siguen iguales.
- Los tests de onboarding, project entry, mejoras y pendientes pasan.

---

## 17. Refactorizar `cli.py`

### Problema

`cli.py` define todos los comandos y ejecuta demasiada lógica.

### No crear carpeta `july/cli/`

Ya existe:

```text
apps/july/july/cli.py
```

Usa:

```text
apps/july/july/commands/
```

### Crear estructura

```text
apps/july/july/commands/
  __init__.py
  output.py
  capture.py
  projects.py
  sessions.py
  topics.py
  skills.py
  references.py
  architect.py
```

### Orden recomendado

#### 17.1 Extraer funciones de impresión

Mover:

```python
print_rows()
print_skill_catalog()
print_capture_result()
print_proactive_hints()
```

a:

```text
apps/july/july/commands/output.py
```

Validar y commit.

#### 17.2 Extraer skills

Mover lógica de comandos:

```text
skill-register
skills
skill-suggest
```

a:

```text
apps/july/july/commands/skills.py
```

Mantén en `cli.py` solo el parser y la llamada.

#### 17.3 Extraer sesiones

Mover:

```text
session-start
session-summary
session-end
session-context
sessions
```

a:

```text
apps/july/july/commands/sessions.py
```

#### 17.4 Extraer proyectos

Mover:

```text
project-entry
project-onboard
project-action
conversation-checkpoint
improvement-add
improvements
improvement-status
pending-add
pendings
pending-status
plug
architect
ui-link
```

a:

```text
apps/july/july/commands/projects.py
```

### Patrón sugerido

```python
# apps/july/july/commands/skills.py

def handle_skill_register(args, database):
    ...

def handle_skills(args, database):
    ...

def handle_skill_suggest(args, database):
    ...
```

En `cli.py`:

```python
if args.command == "skills":
    return handle_skills(args, database)
```

### Mejora posterior

Cuando esté estable, puedes usar `set_defaults(func=...)` en argparse para que cada subcomando sepa qué handler ejecutar.

### Validación

```bash
cd apps/july
python -m unittest discover -s tests
july --help
july skills --registered-only
```

### Criterio de finalización

- `cli.py` baja mucho de tamaño.
- Los comandos actuales no cambian.
- Los tests pasan.
- `july --help` sigue funcionando.

---

## 18. Refactorizar `mcp.py`

### Problema

`mcp.py` mezcla:

- servidor JSON-RPC;
- definición de herramientas;
- schemas;
- handlers;
- serialización;
- lógica de proyectos;
- lógica de skills;
- lógica de memoria;
- lógica de análisis.

### Crear estructura

```text
apps/july/july/mcp_tools/
  __init__.py
  specs.py
  validation.py
  handlers_capture.py
  handlers_projects.py
  handlers_sessions.py
  handlers_skills.py
  handlers_references.py
  handlers_architect.py
```

### Orden recomendado

#### 18.1 Extraer validación

Mover:

```python
require_string()
string_list()
rows_to_dicts()
```

a:

```text
apps/july/july/mcp_tools/validation.py
```

#### 18.2 Extraer specs

Mover la construcción de herramientas a:

```text
apps/july/july/mcp_tools/specs.py
```

Puedes mantener `ToolSpec` en `mcp.py` al principio, o moverlo también.

#### 18.3 Extraer handlers por grupo

Mover poco a poco:

```text
capture_input, search_context, list_inbox, clarify_input, promote_memory
```

a `handlers_capture.py`.

Luego:

```text
project_entry, project_onboard, project_action, plug_project, architect_insights
```

a `handlers_projects.py` o `handlers_architect.py`.

Luego:

```text
skill_register, skill_references, skill_suggest
```

a `handlers_skills.py`.

### Criterio importante

No cambies nombres de tools MCP.

Deben seguir llamándose:

```text
capture_input
project_entry
project_onboard
skill_references
skill_suggest
plug_project
architect_insights
```

### Validación

Añade o mantiene tests para comprobar:

```python
self.assertIn("project_entry", server.tools)
self.assertIn("skill_references", server.tools)
self.assertIn("plug_project", server.tools)
```

Después:

```bash
cd apps/july
python -m unittest discover -s tests
```

### Commit

```bash
git commit -m "refactor: split MCP tool handlers"
```

---

## 19. Revisar seguridad del repo público

### Objetivo

Evitar que memoria sensible, rutas privadas innecesarias o tokens acaben publicados.

### Ejecutar búsqueda manual

Desde raíz del repo:

```bash
git grep -n -i "api key\|apikey\|password\|secret\|token=\|bearer \|sk-\|sb_publishable_\|private key"
```

### Revisar especialmente

```text
context/
context/secure/
context/wiki/log.md
skills/
AGENTS.md
README.md
apps/july/README.md
```

### Qué hacer si aparece algo sensible

1. Eliminarlo del archivo.
2. Añadir patrón a `.gitignore` si corresponde.
3. Si ya fue publicado y es una clave real, rotarla.
4. Si fue publicado en commits anteriores, considerar limpieza de historial.

### Criterio de finalización

- No hay claves ni secretos.
- No hay rutas privadas innecesarias salvo las imprescindibles para documentación.
- `.gitignore` protege bases de datos, exports, `.env`, vaults y cachés.

---

## 20. Mejorar tests

### Tests mínimos que conviene añadir

#### 20.1 Tests de versión

```python
def test_package_version_matches_expected(self):
    import july
    self.assertRegex(july.__version__, r"^\d+\.\d+\.\d+$")
```

#### 20.2 Tests de repositorios

Después de extraer repositorios, añade tests específicos para:

```text
SkillRepository
SessionRepository
ProjectRepository
TaskRepository
TopicRepository
```

#### 20.3 Tests de migraciones

Crear base con esquema antiguo y comprobar que se actualiza.

#### 20.4 Tests CLI básicos

Comprobar que existen comandos:

```python
self.assertIn("skills", choices)
self.assertIn("project-entry", choices)
self.assertIn("session-start", choices)
```

Ya hay parte de esto. Amplíalo según refactorices.

#### 20.5 Tests MCP básicos

Comprobar que las tools siguen expuestas.

---

## 21. Revisión final de estructura esperada

Al terminar, la estructura debería parecerse a esto:

```text
apps/july/july/
  __init__.py
  analyzer.py
  cli.py
  config.py
  db.py
  mcp.py
  pipeline.py
  project_conversation.py
  skill_registry.py
  url_fetcher.py

  storage/
    __init__.py
    schema.py
    migrations.py
    utils.py

  repositories/
    __init__.py
    skill_repository.py
    project_repository.py
    session_repository.py
    task_repository.py
    memory_repository.py
    topic_repository.py
    reference_repository.py
    search_repository.py
    developer_repository.py

  project/
    __init__.py
    identity.py
    surface.py
    profile.py
    messages.py
    checkpoints.py

  commands/
    __init__.py
    output.py
    capture.py
    projects.py
    sessions.py
    topics.py
    skills.py
    references.py
    architect.py

  mcp_tools/
    __init__.py
    specs.py
    validation.py
    handlers_capture.py
    handlers_projects.py
    handlers_sessions.py
    handlers_skills.py
    handlers_references.py
    handlers_architect.py
```

Importante: `db.py`, `cli.py`, `mcp.py` y `project_conversation.py` pueden seguir existiendo como fachadas. No hace falta eliminarlos.

---

## 22. Orden de commits recomendado

```text
ci: add July test workflow
chore: align July package version
refactor: extract database schema utilities
refactor: extract skill repository
refactor: extract session repository
refactor: extract project repository
refactor: extract task and improvement repository
refactor: extract memory read repository
refactor: extract memory capture repository
refactor: extract topic repository
refactor: extract reference repository
refactor: extract search repository
refactor: add explicit schema migrations
refactor: extract project identity helpers
refactor: extract project surface analysis
refactor: extract project profile inference
refactor: extract project conversation messages
refactor: extract project checkpoints
refactor: extract CLI output helpers
refactor: split CLI command handlers
refactor: split MCP validation helpers
refactor: split MCP tool specs
refactor: split MCP tool handlers
test: add repository and migration coverage
docs: update July architecture after refactor
```

---

## 23. Comandos de verificación final

Desde `apps/july`:

```bash
python -m pip install -e .
python -m unittest discover -s tests
python -c "import july; print(july.__version__)"
july --help
july stats
july skills --registered-only
```

Si usas Windows:

```powershell
py -3.11 -m pip install -e .
py -3.11 -m unittest discover -s tests
py -3.11 -c "import july; print(july.__version__)"
july --help
july stats
july skills --registered-only
```

---

## 24. Qué no hacer todavía

No hagas esto al principio:

- No migres todo a SQLAlchemy.
- No cambies nombres de comandos CLI.
- No cambies nombres de tools MCP.
- No reescribas la base de datos.
- No añadas una UI nueva antes de ordenar el núcleo.
- No elimines `JulyDatabase`; mantenlo como fachada.
- No metas nuevas capacidades grandes mientras `db.py`, `cli.py` y `mcp.py` sigan concentrando tanta lógica.

---

## 25. Criterio final de éxito

El refactor estará bien hecho cuando:

- La versión del paquete y la documentación estén alineadas.
- GitHub Actions ejecute tests automáticamente.
- `db.py` sea principalmente una fachada.
- La lógica de persistencia esté repartida en repositorios.
- `cli.py` sea principalmente parser y dispatcher.
- `mcp.py` sea principalmente servidor y registro de tools.
- `project_conversation.py` tenga menos helpers mezclados.
- Los comandos existentes sigan funcionando.
- Las tools MCP mantengan sus nombres.
- Los tests pasen.
- El README y ROADMAP expliquen la nueva arquitectura.

---

## 26. Siguiente paso recomendado

Empieza por estos tres cambios, en este orden:

1. Alinear versión.
2. Añadir CI.
3. Extraer `storage/schema.py` y `storage/utils.py`.

No empieces por `mcp.py`. No empieces por `project_conversation.py`. Primero estabiliza tests y base de datos.
