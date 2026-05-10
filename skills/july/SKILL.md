---
name: july
description: Atajo corto para usar July como memoria local de proyecto. Usar cuando Sergio invoque /july, quiera arrancar sesión, recuperar contexto, ver pendientes o guardar conocimiento operativo.
---

# Skill: /july

Atajo corto para trabajar con July desde cualquier proyecto.

## Cuándo se usa

Cuando Sergio escribe `/july`, `/july <objetivo>` o pide recuperar memoria de proyecto sin usar el nombre largo `/july-inicio`.

## Lo que debes hacer

Sigue el mismo procedimiento de `skills/july-inicio/SKILL.md`:

1. Detecta el proyecto actual con `mcp__july__project_entry`.
2. Abre sesión con `mcp__july__session_start`.
3. Recupera contexto reciente con `mcp__july__session_context`.
4. Consulta pendientes abiertos con `mcp__july__project_pendings`.
5. Resume el estado en español claro y espera la siguiente instrucción.

## Variantes útiles

- `/july <objetivo>`: usa `<objetivo>` como `goal` al abrir sesión.
- Si Sergio pregunta por ayuda, responde como `/july-ayuda`.
- Si Sergio pide comprimir contexto, aplica `/july-comprimir`.

## Notas

- Usa `agent_name: "Claude"` en Claude Code o `agent_name: "Codex"` en Codex.
- No hagas onboarding completo salvo que el proyecto sea nuevo y Sergio lo confirme.
- Al cerrar una sesión, usa `mcp__july__session_summary` y `mcp__july__session_end`.
