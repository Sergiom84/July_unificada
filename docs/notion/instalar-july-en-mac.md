# Procedimiento: instalar y usar July en Mac

## Objetivo

Instalar July en macOS desde `July_unificada`, dejar claro qué viaja por Git y qué vive fuera del repositorio, y tener un prompt de arranque para que Codex o Claude usen July como memoria local antes de tocar código.

Resumen clave:

- Git lleva el cerebro curado: wiki, docs, procedimientos y código de July.
- `~/.july/july.db` lleva la memoria viva: sesiones, proyectos, mejoras, pendientes y recall operativo.
- La base de datos viva no debe guardarse en Git.

## Lectura inicial

Antes de instalar, revisar en este orden:

1. `AGENTS.md`
2. `README.md`
3. `context/wiki/index.md`
4. `apps/july/README.md`
5. `apps/july/ROADMAP.md`
6. `apps/july/PROJECT_PROTOCOL.md`

## Instalar July en Mac

Desde la carpeta del repo unificado:

```bash
cd ~/Desktop/Aplicaciones/July_unificada/apps/july
python3 -m venv .venv
.venv/bin/pip install -e .
chmod +x scripts/*.sh start-july-mcp.sh
./scripts/july.sh stats
```

July usará por defecto:

```text
~/.july/july.db
```

## Copiar la memoria viva desde Windows

Si el Mac debe tener la memoria operativa real de Windows, copiar la base de datos viva:

```text
Windows: C:\Users\sergi\.july\july.db
Mac:     ~/.july/july.db
```

Si no se copia esa base de datos, el Mac tendrá la wiki, docs y código del repo, pero no tendrá las sesiones, proyectos, mejoras ni pendientes guardados previamente en July.

## Prompt de arranque para Codex o Claude

Copiar este prompt al abrir un proyecto:

```text
Usa July como memoria local.

Antes de tocar código:
1. Lee AGENTS.md, README.md y CLAUDE.md si existen en este proyecto.
2. Consulta July con project-entry para este repo.
3. Consulta ~/Desktop/Aplicaciones/July_unificada/context/wiki/index.md y páginas relevantes.
4. Dime si este proyecto es nuevo, conocido o parcial.
5. Resume qué sabes, qué falta y qué siguiente paso propones.

Reglas:
- No tocar código hasta tener claro el objetivo.
- Guardar decisiones, hallazgos, mejoras y pendientes cuando proceda.
- Si algo es una idea opcional, guardarlo como mejora.
- Si algo es trabajo por hacer, guardarlo como pendiente.
```

## Comandos útiles

Desde cualquier proyecto, si July está instalado:

```bash
~/Desktop/Aplicaciones/July_unificada/apps/july/scripts/july.sh project-entry --repo-path "$(pwd)"
~/Desktop/Aplicaciones/July_unificada/apps/july/scripts/july.sh improvements --repo-path "$(pwd)"
~/Desktop/Aplicaciones/July_unificada/apps/july/scripts/july.sh pendings --repo-path "$(pwd)"
```

Atajos esperados en agente:

```text
/july
/mejoras
/pendiente <texto>
/pendientes
/ayuda
```

## MCP en Mac

Configurar Claude o Codex con este servidor MCP, ajustando la ruta real del usuario:

```json
{
  "mcpServers": {
    "july": {
      "command": "bash",
      "args": ["/Users/sergio/Desktop/Aplicaciones/July_unificada/apps/july/start-july-mcp.sh"],
      "cwd": "/Users/sergio/Desktop/Aplicaciones/July_unificada/apps/july"
    }
  }
}
```

Si el usuario de macOS o la ubicación del repo son distintos, cambiar `/Users/sergio/Desktop/Aplicaciones/July_unificada` por la ruta real.

## Regla práctica

Git sincroniza la memoria curada. `~/.july/july.db` sincroniza la memoria viva. Mantener ambas capas separadas evita subir sesiones, proyectos o datos operativos a Git por accidente.
