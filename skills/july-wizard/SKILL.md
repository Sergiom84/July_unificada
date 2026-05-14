---
name: july-wizard
description: Onboarding read-only para conectar un proyecto nuevo o parcial a July. Usar cuando Sergio invoque /july-wizard, pida una primera foto del repo o quiera preparar memoria operativa inicial del proyecto.
---

# Skill: /july-wizard

Wizard de onboarding para July. Su función es crear o refrescar una primera foto útil del proyecto, no trabajar en la feature ni modificar código.

## Cuándo se usa

- Sergio invoca `/july-wizard`.
- `/july` o `/july-inicio` detectan proyecto nuevo o contexto parcial y Sergio acepta onboarding.
- Sergio pide conectar un repo a July, preparar memoria inicial o revisar qué sabe July del proyecto.

Para un arranque normal de proyecto conocido, usa `/july-inicio`.

## Lo que debes hacer

1. Ejecuta `project_entry` con el directorio actual.
2. Recupera `project_context` y `session_context` si existe `project_key`.
3. Explica si July ve el proyecto como `new`, `partial` o `known`, y qué falta para que sea útil.
4. Pide permiso antes de leer el repo de forma amplia o ejecutar `project_onboard` / `project_action analyze_now`.
5. Si Sergio acepta, haz onboarding read-only:
   - lee documentación real visible (`README`, `AGENTS`, manifiestos, entrypoints);
   - identifica objetivo, stack, arquitectura, comandos, integraciones, riesgos y dudas;
   - guarda memoria operativa en July, no en la wiki, salvo que sea conocimiento curado entre proyectos.
6. Si aparece un patrón reusable entre proyectos, propón guardarlo en `context/wiki/` o `docs/notion/`, pero no lo hagas sin petición explícita.

## Salida esperada

Resume:

- Estado del proyecto en July.
- Qué sabe July ahora.
- Stack y estructura visible.
- Reglas locales relevantes.
- Pendientes, mejoras o riesgos.
- Siguiente acción recomendada.

## Límites

- No edites código durante el onboarding salvo petición explícita.
- No guardes secretos ni valores de `.env`.
- No trates un proyecto como conocido solo por tener un item aislado: debe existir contexto suficiente para retomar trabajo real.
- No repitas onboarding completo si basta un refresh selectivo.

## Fallback CLI

```powershell
cd C:\Users\sergi\Desktop\Aplicaciones\July_unificada
.\scripts\july.ps1 project-entry --repo-path <repo-actual>
.\scripts\july.ps1 project-action help --repo-path <repo-actual> --agent codex
.\scripts\july.ps1 project-action analyze_now --repo-path <repo-actual> --agent codex
```

## Notas

- Habla siempre en español con tildes correctas.
- No inventes contexto: marca incertidumbre.
- Si el onboarding deja una sesión real abierta, ciérrala con `session_summary` y `session_end` al terminar.
