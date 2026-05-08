---
type: analysis
status: active
created: 2026-05-08
updated: 2026-05-08
sources:
  - context/wiki/entities/mhk-studio.md
  - context/wiki/concepts/web-de-cliente-para-captacion.md
  - context/wiki/concepts/fuente-unica-de-datos-de-negocio.md
  - context/wiki/concepts/formularios-con-envio-real.md
  - C:/Users/sergi/Desktop/Aplicaciones/Marta Harranz/Mhkstudio/package.json
  - C:/Users/sergi/Desktop/Aplicaciones/Marta Harranz/Mhkstudio/render.yaml
  - C:/Users/sergi/Desktop/Aplicaciones/Marta Harranz/Mhkstudio/src/data/locations.ts
tags:
  - piloto
  - web-cliente
  - mhk-studio
  - arranque
---

# Piloto de arranque MHK Studio

## Objetivo

Probar el comportamiento del prompt de arranque con una web real usando la memoria local de `Mente_unificada`.

## Proyecto

Ruta:

`C:\Users\sergi\Desktop\Aplicaciones\Marta Harranz\Mhkstudio`

Tipo:

Web de cliente para captacion, interiorismo, Astro, SEO local por ciudades y formularios HubSpot.

## Contexto recuperado de la memoria

Paginas consultadas:

- [[Web de cliente para captacion]]
- [[Fuente unica de datos de negocio]]
- [[Formularios con envio real]]
- [[MHK Studio]]

La memoria anticipaba estos puntos:

- falta `AGENTS.md` propio en el proyecto;
- README generico de Astro pendiente de adaptar;
- `siteConfig` como fuente unica de datos;
- SEO local por ciudades;
- riesgo de formularios y deploy.

## Observaciones del repo

- No existe `AGENTS.md`.
- El README sigue siendo el starter de Astro.
- Hay `siteConfig` en `src/data/locations.ts` con nombre, URL, telefono, email, direccion, redes y WhatsApp.
- Hay paginas SEO locales generadas desde `locations`.
- El formulario ya no parece Netlify; usa HubSpot con `portalId` y `formId`.
- Hay `render.yaml` con deploy static en Render, pero tambien existe script `deploy:cloudflare` y `wrangler.toml`.
- `render.yaml` contiene rewrite global `/* -> /index.html`, que conviene revisar en un sitio Astro multipagina.
- El repo tiene cambios locales sin commitear antes de cualquier intervencion.

## Diagnostico inicial

El comportamiento de la memoria fue util: permitio revisar primero los riesgos correctos en vez de mirar el repo sin criterio.

La prioridad no deberia ser programar directamente, sino ordenar el contrato del proyecto:

1. Crear `AGENTS.md` propio para MHK Studio.
2. Actualizar README con comandos, stack, deploy real y decisiones.
3. Aclarar plataforma final de deploy: Render o Cloudflare Pages.
4. Confirmar que los formularios HubSpot envian correctamente en produccion.
5. Revisar si el rewrite global de Render es correcto para Astro static multipagina.

## Regla extraida

Al conectar una web existente a `Mente_unificada`, el primer paso debe ser diagnostico read-only:

- instrucciones locales;
- README;
- package/deploy;
- fuente unica de datos;
- formularios;
- SEO;
- estado Git;
- divergencias entre memoria previa y repo actual.

Solo despues conviene modificar codigo o documentacion.

## Relacionado

- [[Memoria unificada para programar]]
- [[MHK Studio]]
- [[Web de cliente para captacion]]
- [[Formularios con envio real]]
