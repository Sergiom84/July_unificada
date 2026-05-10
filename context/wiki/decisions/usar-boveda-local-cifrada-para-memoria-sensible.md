---
type: decision
status: active
created: 2026-05-09
updated: 2026-05-09
sources:
  - context/secure/README.md
tags:
  - memoria
  - seguridad
  - july
  - cifrado-local
---

# Usar bóveda local cifrada para memoria sensible

Se decide que July forme parte de la mente unificada, pero sin almacenar secretos.

## Decisión

Cuando haya información de acceso operativo que convenga recordar:

- July guardará el nombre del proyecto, herramienta, MCP, workspace o puntero lógico.
- `Mente_unificada` guardará contenido sensible solo en la bóveda local cifrada.
- Las páginas wiki normales solo documentarán el procedimiento y los punteros no secretos.

## Motivo

July es útil para recuperar contexto entre sesiones, pero no debe recibir tokens, claves, passwords, `DATABASE_URL`, service-role keys ni valores crudos de `.env`.

La bóveda local permite guardar material cifrado en la máquina de Sergio y abrirlo solo cuando haga falta.

## Procedimiento

Usar:

```powershell
.\scripts\secure-memory.ps1 -Action seal -Key "proyecto/tema"
.\scripts\secure-memory.ps1 -Action open -Key "proyecto/tema"
```

La clave lógica debe describir el contenido sin revelar secretos.
