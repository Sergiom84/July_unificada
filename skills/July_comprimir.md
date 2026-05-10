# Skill: /July_comprimir

Wrapper seguro sobre caveman-compress. Comprime un fichero de procedimientos o conocimiento usando Claude, con verificación de ruta antes de actuar.

## Cuándo se usa

Cuando el usuario quiere comprimir un fichero largo para reducir tokens, o cuando July sugiere usar Caveman porque la conversación se está alargando.

## Lo que debes hacer

### Paso 1 — Identificar el fichero

Si el usuario no indicó un fichero concreto, pregúntale cuál quiere comprimir antes de continuar.

### Paso 2 — Verificar la ruta

**Rechaza y avisa si la ruta coincide con alguno de estos patrones:**

| Patrón | Razón |
|---|---|
| `*.env`, `.env.*` | Puede contener claves o tokens |
| `context/secure/` | Memoria sensible cifrada |
| `*.db`, `july.db` | Base de datos de July |
| `*credentials*`, `*secret*`, `*token*`, `*key*` | Nombres que sugieren secretos |
| Cualquier fichero > 500 KB | Límite de la herramienta |

Si la ruta es segura, continúa. Si no, di exactamente por qué la rechazas y no ejecutes nada.

### Paso 3 — Confirmar

Muestra al usuario:
- Ruta del fichero
- Que se creará una copia de seguridad en `<fichero>.original.md`
- Que el contenido se enviará a Claude/Anthropic para comprimirlo

Pide confirmación explícita antes de continuar.

### Paso 4 — Ejecutar caveman-compress

Solo tras confirmación, invoca caveman-compress sobre el fichero indicado.

### Paso 5 — Informar

Tras la compresión:
- Confirma que se creó la copia `.original.md`
- Indica cuánto se redujo el fichero si es posible
- Recuerda que puede revertirse con: `mv <fichero>.original.md <fichero>.md`

## Notas

- Este skill NO reemplaza caveman-compress: es una capa de seguridad encima.
- Úsalo especialmente en ficheros de `~/.claude/skills/`, `context/wiki/`, `docs/notion/` y `AGENTS.md`.
- En reviews de seguridad, arquitectura u onboarding, sugiere desactivar el modo comprimido de caveman-review.
- Habla siempre en español con tildes correctas.
