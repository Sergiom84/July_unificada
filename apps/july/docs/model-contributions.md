# Contribuciones históricas de modelos

Este documento consolida las propuestas antiguas que estaban en la raíz de `apps/july` como `July_Genspark.txt`, `July_Z.AI.txt` y `July_GPT.txt`.

Las propuestas no son documentos rectores. Funcionan como referencias históricas reconciliadas con la dirección actual de July:

- local-first;
- single-user;
- SQLite + FTS5;
- CLI/MCP/cockpit como infraestructura;
- memoria operativa en July;
- criterio curado en `context/wiki/`.

## Genspark

Planteaba una visión amplia apoyada en Engram, Gentle AI, Obsidian, OpenSpec y sincronización cloud.

Valor absorbido:

- arquitectura por capas fácil de visualizar;
- MCP como interfaz universal;
- separación entre memoria técnica y memoria personal;
- importancia de estructura por proyecto.

No adoptado como punto de partida:

- enfoque de equipo;
- sincronización cloud como prioridad;
- Engram como núcleo obligatorio;
- Obsidian como almacenamiento principal.

## Z.AI

Empujaba una postura pragmática: SQLite + FTS5 + MCP como base local, curación por agente y memoria compartida entre herramientas.

Valor absorbido:

- arranque sencillo y útil;
- evitar Google Docs como núcleo;
- memoria local propia antes que dependencia externa;
- agente responsable de guardar memoria curada.

## GPT

Aportaba una lectura más amplia de arquitectura de producto y flujo de captura, memoria y orquestación.

Valor absorbido:

- separar captura, memoria y orquestación;
- tratar Google Docs como fuente opcional, no como base;
- combinar búsqueda literal, metadatos y capa MCP/API;
- mantener la visión de conocimiento reutilizable entre proyectos.

## Estado

Las decisiones vivas están en `apps/july/README.md`, `apps/july/ROADMAP.md`, `apps/july/PROJECT_PROTOCOL.md` y `AGENTS.md`.

La visión inicial propia de July queda archivada como documento histórico en `docs/initial-vision.md`.

Las copias legacy completas quedan en los backups de migración, no en la raíz activa de la app.
