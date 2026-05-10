# July_unificada

`July_unificada` es el espacio local de memoria y copiloto de Sergio.

Une dos capas que deben seguir separadas conceptualmente:

- `context/` y `docs/`: memoria curada, wiki, procedimientos, decisiones y prompts reutilizables.
- `apps/july/`: motor operativo July para sesiones, proyectos, recall, MCP, CLI y cockpit.

La base de datos viva de July no debe guardarse dentro de este repositorio. El valor por defecto sigue siendo:

```text
C:\Users\sergi\.july\july.db
```

## Estructura

```text
July_unificada/
  apps/
    july/
  context/
    raw/
    wiki/
  docs/
    notion/
  scripts/
  skills/
  AGENTS.md
  roadmap.md
```

## Flujo esperado

1. Un agente entra en un proyecto real.
2. Usa `july-wizard` para recuperar contexto desde July.
3. Consulta `context/wiki/index.md` cuando necesite criterio curado.
4. Trabaja sobre el repo real.
5. Guarda en July avances, decisiones y próximos pasos.
6. Destila a `context/wiki/` solo lo que se vuelva patrón o decisión estable.

## Regla práctica

July recuerda la sesión. La wiki conserva el criterio.
