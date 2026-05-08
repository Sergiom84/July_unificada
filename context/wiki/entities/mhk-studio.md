---
type: entity
status: active
created: 2026-05-08
updated: 2026-05-08
sources:
  - docs/notion/webs-analisis-inicial.md
tags:
  - proyecto
  - web-cliente
  - astro
  - seo-local
---

# MHK Studio

Proyecto en desarrollo de estudio de interiorismo con Astro, Tailwind y SEO local por ciudades.

## Stack

Astro 6, Tailwind 4, sitemap y Render static.

## Valor como plantilla

Plantilla moderna para web estatica SEO local, especialmente para negocios con varias zonas de servicio.

## Puntos fuertes

- `siteConfig` centraliza nombre, descripcion, URL, telefono, email, direccion y redes.
- `locations.ts` permite crear paginas SEO por ciudad con `getStaticPaths`.
- `Layout.astro` concentra metadatos, Open Graph, Twitter Card y schema sitewide.
- Base fuerte para webs de cliente estaticas con SEO local.

## Riesgos o pendientes

- README generico de Astro pendiente de adaptar.
- Formulario con Netlify Forms aunque el deploy es Render.
- Revisar si la ruta rewrite de Render para SPA encaja con un sitio Astro estatico multipagina.
- Falta `AGENTS.md` propio en ese proyecto.

## Relacionado

- [[SEO local para webs de cliente]]
- [[Fuente unica de datos de negocio]]
- [[Formularios con envio real]]
- [[Analisis inicial de webs de cliente]]
