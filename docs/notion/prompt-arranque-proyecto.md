# Prompt de arranque: web, app o software

Usar este prompt al empezar con una web, app o software nuevo o ya existente.

```text
Actúa como mi agente de desarrollo usando mi memoria local.

Proyecto actual:
[pega aquí ruta, nombre y objetivo breve del proyecto]

Antes de proponer o tocar nada:
1. Lee las instrucciones locales del proyecto si existen: AGENTS.md, README.md, ROADMAP.md o similares.
2. Lee la memoria compartida en:
   C:\Users\sergi\Desktop\Aplicaciones\July_unificada\context\wiki\index.md
3. Abre las páginas relevantes de concepts, decisions y analyses.
4. Si el trabajo es una web de cliente, aplica especialmente:
   - Web de cliente para captación
   - Fuente única de datos de negocio
   - Formularios con envío real
   - SEO local para webs de cliente
   - Centralizar datos de negocio
   - Validar formularios en deploy
5. Si July está disponible, recupera contexto operativo del proyecto antes de pedirme que repita información.

Después dame primero un diagnóstico corto:
- qué es este proyecto;
- qué contexto previo has encontrado;
- qué riesgos o decisiones de la memoria aplican;
- qué falta por confirmar;
- cuál sería el siguiente paso más razonable.

Reglas:
- No subas nada a servicios externos.
- No guardes secretos ni valores crudos de .env.
- No hagas cambios de código hasta terminar el diagnóstico inicial, salvo que te pida ejecutar directamente.
- Si aparece una decisión reutilizable, propón si debe guardarse como memoria operativa en July o como criterio curado en `context/wiki/`.
```

## Versión corta

```text
Arranca este proyecto usando mi memoria local.
Lee el AGENTS/README del proyecto, después `July_unificada/context/wiki/index.md` y páginas relevantes.
Si es una web de cliente, aplica los patrones de captación, fuente única de datos, SEO y formularios reales.
Primero dame diagnóstico y siguiente paso. No subas nada ni guardes secretos.
```
