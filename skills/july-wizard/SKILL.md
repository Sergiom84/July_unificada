---
name: july-wizard
description: Project memory wizard for July. Usar cuando Sergio invoque /july-wizard o quiera conectar un proyecto nuevo a July con una primera foto del repo.
---

# Skill: /july-wizard

Wizard de memoria de proyecto para July.

## Cuándo se usa

Cuando Sergio quiere preparar un proyecto para que July lo recuerde: detectar stack, reglas locales, estado inicial, pendientes y próximos pasos.

## Lo que debes hacer

1. Ejecuta `mcp__july__project_entry` con el directorio actual.
2. Si el proyecto ya es conocido, recupera contexto con `mcp__july__session_context` y pregunta si quiere continuar desde ahí.
3. Si el proyecto es nuevo o parcial, propone onboarding read-only antes de guardar nada.
4. Si Sergio acepta, ejecuta `mcp__july__plug_project`.
5. Guarda solo memoria operativa en July: stack, comandos, reglas críticas, riesgos, pendientes y siguiente paso.
6. No edites código durante el onboarding salvo petición explícita.

## Salida esperada

Resume:

- Estado del proyecto en July: nuevo, parcial o conocido.
- Stack y estructura detectados.
- Reglas locales relevantes.
- Pendientes o riesgos.
- Siguiente acción recomendada.

## Notas

- Habla siempre en español con tildes correctas.
- No inventes contexto: si falta información, marca incertidumbre.
- Si aparece conocimiento reusable entre proyectos, propón guardarlo en `context/wiki/` o `docs/notion/`.
