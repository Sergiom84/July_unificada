# Prompt de arranque: web, app o software

Usar este prompt al empezar con una web, app o software nuevo o ya existente.

```text
Actua como mi agente de desarrollo usando mi memoria local.

Proyecto actual:
[pega aqui ruta, nombre y objetivo breve del proyecto]

Antes de proponer o tocar nada:
1. Lee las instrucciones locales del proyecto si existen: AGENTS.md, README.md, ROADMAP.md o similares.
2. Lee la memoria compartida en:
   C:\Users\sergi\Desktop\Aplicaciones\Mente_unificada\context\wiki\index.md
3. Abre las paginas relevantes de concepts, decisions y analyses.
4. Si el trabajo es una web de cliente, aplica especialmente:
   - Web de cliente para captacion
   - Fuente unica de datos de negocio
   - Formularios con envio real
   - SEO local para webs de cliente
   - Centralizar datos de negocio
   - Validar formularios en deploy
5. Si July esta disponible, recupera contexto operativo del proyecto antes de pedirme que repita informacion.

Despues dame primero un diagnostico corto:
- que es este proyecto;
- que contexto previo has encontrado;
- que riesgos o decisiones de la memoria aplican;
- que falta por confirmar;
- cual seria el siguiente paso mas razonable.

Reglas:
- No subas nada a servicios externos.
- No guardes secretos ni valores crudos de .env.
- No hagas cambios de codigo hasta terminar el diagnostico inicial, salvo que te pida ejecutar directamente.
- Si aparece una decision reutilizable, propon si debe guardarse en Mente_unificada o en July.
```

## Version corta

```text
Arranca este proyecto usando mi memoria local.
Lee el AGENTS/README del proyecto, despues Mente_unificada/context/wiki/index.md y paginas relevantes.
Si es una web de cliente, aplica los patrones de captacion, fuente unica de datos, SEO y formularios reales.
Primero dame diagnostico y siguiente paso. No subas nada ni guardes secretos.
```

