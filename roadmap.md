# Roadmap de migración a July_unificada

Objetivo: fusionar físicamente `Mente_unificada` y `July` en una sola carpeta llamada `July_unificada`, manteniendo separadas las responsabilidades internas:

- `context/` y `docs/`: memoria curada, wiki, decisiones, procedimientos y prompts.
- `apps/july/`: motor operativo July, CLI, MCP, cockpit, sesiones y recall.
- `skills/`: skills y rituales locales del copiloto.
- `scripts/`: wrappers cómodos para no memorizar rutas internas.

La regla principal es no perder información ni romper el flujo ya validado con `july-wizard`.

## Principios de seguridad

- No borrar carpetas originales durante la migración.
- No copiar secretos a nuevas ubicaciones si no son necesarios.
- Mantener la base de datos viva fuera del repo: `C:\Users\sergi\.july\july.db`.
- Excluir entornos generados: `.venv`, `__pycache__`, `july.egg-info`, bases temporales y caches.
- Verificar cada hito antes de pasar al siguiente.
- Si un check falla, parar y documentar el bloqueo.

## Estado inicial detectado

| Elemento | Estado |
| --- | --- |
| `C:\Users\sergi\Desktop\Aplicaciones\Mente_unificada` | Existe y contiene la wiki/procedimientos |
| `C:\Users\sergi\Desktop\Aplicaciones\July` | Existe y contiene el motor July |
| `C:\Users\sergi\Desktop\Aplicaciones\July_unificada` | No existe al inicio |
| Git en `Mente_unificada` | Worktree con cambios sin commitear |
| Git en `July` | Worktree con cambios sin commitear |
| BD global July | Debe seguir en `C:\Users\sergi\.july\july.db` |

## Hito 0: inventario

Objetivo: confirmar carpetas, Git y riesgos antes de tocar estructura.

Checks:

- [x] Existe `Mente_unificada`.
- [x] Existe `July`.
- [x] No existe `July_unificada`.
- [x] Detectados cambios sin commitear en ambos proyectos.
- [x] Decisión: migración no destructiva, con backups y sin borrar originales.

## Hito 1: crear este roadmap

Objetivo: dejar por escrito el procedimiento antes de ejecutar la migración.

Checks:

- [x] `roadmap.md` existe en la raíz actual.
- [x] El documento enumera hitos, checks y criterios de seguridad.
- [x] El avance queda registrado en `context/wiki/log.md`.

## Hito 2: backups no destructivos

Objetivo: crear copias de seguridad antes de mover o renombrar carpetas.

Acciones:

1. Crear carpeta de backup fuera de ambos proyectos.
2. Copiar `Mente_unificada` excluyendo `.git` si el backup operativo no necesita historial.
3. Copiar `July` excluyendo `.venv`, caches, temporales y bases duplicables.
4. No mostrar ni imprimir contenido de `.env`.

Checks:

- [x] Existe backup de `Mente_unificada`.
- [x] Existe backup de `July`.
- [x] El backup no contiene `.venv`.
- [x] El backup no contiene bases temporales innecesarias.

Backup creado:

```text
C:\Users\sergi\Desktop\Aplicaciones\_migration_backups\July_unificada_20260509-233901
```

## Hito 3: preparar estructura unificada

Objetivo: convertir la raíz actual de `Mente_unificada` en la futura raíz de `July_unificada`.

Estructura objetivo:

```text
July_unificada/
  AGENTS.md
  CLAUDE.md
  README.md
  roadmap.md
  apps/
    july/
  context/
  docs/
  scripts/
  skills/
```

Checks:

- [x] Existe `apps/`.
- [x] Existe `skills/`.
- [x] `context/` y `docs/` siguen intactos.
- [x] `AGENTS.md` describe la nueva estructura.

## Hito 4: copiar July dentro de `apps/july`

Objetivo: integrar el motor July dentro del monorepo sin arrastrar basura generada ni secretos.

Excluir:

- `.git`
- `.venv`
- `.env`
- `july.egg-info`
- `__pycache__`
- `.pytest_cache`
- `tmp-ui-smoke.db`
- bases locales duplicadas si no son la fuente global

Checks:

- [x] Existe `apps/july/pyproject.toml`.
- [x] Existe `apps/july/july/`.
- [x] Existe `apps/july/tests/`.
- [x] No existe `apps/july/.env`.
- [x] No existe `apps/july/.venv`.

## Hito 5: wrappers y validación

Objetivo: que July funcione desde la carpeta unificada.

Acciones:

1. Crear wrappers raíz:
   - `scripts/july.ps1`
   - `scripts/ui.ps1`
   - `scripts/mcp.ps1`
2. Ejecutar tests desde `apps/july`.
3. Probar `project-entry` sobre un proyecto conocido.

Checks:

- [x] `scripts/july.ps1 stats` funciona.
- [x] Tests de July pasan.
- [x] `project-entry` puede leer la BD global.

Validación ejecutada:

```powershell
.\scripts\july.ps1 stats
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\scripts\july.ps1 project-entry --repo-path C:\Users\sergi\Desktop\Aplicaciones\Indalo_padel --project-key indalo-padel
```

Resultado:

- `stats`: July lee la BD global y devuelve contadores.
- `tests`: suite de July OK (56 tests en la validación de cierre del 2026-05-16).
- `project-entry`: `indalo-padel` aparece como `known`.

## Hito 6: renombrar raíz

Objetivo: cambiar `Mente_unificada` a `July_unificada`.

Acciones:

1. Verificar que `C:\Users\sergi\Desktop\Aplicaciones\July_unificada` no existe.
2. Renombrar `Mente_unificada` a `July_unificada`.
3. Actualizar referencias críticas:
   - `july-wizard`
   - documentación raíz
   - wrappers
   - enlaces operativos conocidos

Checks:

- [x] Existe `C:\Users\sergi\Desktop\Aplicaciones\July_unificada`.
- [x] Ya no existe la carpeta raíz antigua como carpeta activa.
- [x] `july-wizard` apunta a la nueva ruta.
- [x] La wiki abre desde la nueva ruta.

Nota de ejecución:

- El renombrado directo de `Mente_unificada` a `July_unificada` fue bloqueado por Windows porque la carpeta estaba en uso.
- Se aplicó la vía segura: crear `July_unificada` como copia activa verificada.
- El 2026-05-16 se archivó `Mente_unificada` en `_migration_backups/archived-original-roots-20260516-2255/`.
- La carpeta original `July` ya no existe como raíz activa en `C:\Users\sergi\Desktop\Aplicaciones`; queda respaldo histórico en `_migration_backups/July_unificada_20260509-233901/July`.

## Hito 7: cierre y verificación final

Objetivo: dejar constancia y confirmar que el copiloto sigue funcionando.

Checks:

- [x] `roadmap.md` marca la migración completada.
- [x] `context/wiki/log.md` registra la migración.
- [x] July responde a `project-entry`.
- [x] Una conversación nueva puede usar `july-wizard` con la nueva ruta.
- [x] Las raíces originales quedan fuera de las carpetas activas.

Estado final:

- `July_unificada` queda operativa como carpeta activa.
- `Mente_unificada` quedó archivada en `_migration_backups/archived-original-roots-20260516-2255/Mente_unificada`.
- `July` original no existe como carpeta activa; su respaldo de migración está en `_migration_backups/July_unificada_20260509-233901/July`.
- Pendiente operativo: mantener los backups, pero no usarlos como raíz activa.

## Decisión cerrada

La carpeta activa única es:

```text
C:\Users\sergi\Desktop\Aplicaciones\July_unificada
```

Las raíces anteriores quedan como material histórico en `_migration_backups/`, no como proyectos activos.
