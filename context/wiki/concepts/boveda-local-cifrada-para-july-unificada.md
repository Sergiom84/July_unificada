---
type: concept
status: active
created: 2026-05-09
updated: 2026-05-16
sources:
  - context/secure/README.md
tags:
  - memoria
  - july
  - seguridad
  - cifrado-local
---

# Bóveda local cifrada para July_unificada

La memoria unificada se divide en dos capas:

- **July**: recuerda el proyecto, el flujo operativo, etiquetas, punteros y decisiones no sensibles.
- **Wiki curada**: conserva criterio procedimental.
- **Bóveda local**: guarda referencias cifradas en `context/secure/vault/` cuando haga falta.

Para datos sensibles o semisensibles, la regla es:

1. No guardar secretos en July.
2. No escribir secretos en páginas wiki normales.
3. Guardar el contenido delicado en `context/secure/vault/` usando el script `scripts/secure-memory.ps1`.
4. Guardar en July solo un puntero lógico, por ejemplo `indalo-padel/mcp-tooling`.
5. Abrir el contenido solo bajo petición explícita y en la máquina local.

## Implementación

El script `scripts/secure-memory.ps1` usa DPAPI de Windows con ámbito `CurrentUser`. Esto significa que no hay una clave maestra escrita en el repositorio: Windows protege el material cifrado para el usuario actual.

Los archivos cifrados tienen extensión `.dpapi.json` y están ignorados por Git.

## Límite importante

Este mecanismo protege reposo local accidental y evita persistir secretos en memoria de agentes. No sustituye a un gestor de secretos profesional para producción. Para despliegues y servicios externos, los secretos reales deben seguir viviendo en el proveedor correspondiente o en `.env` local no versionado.
