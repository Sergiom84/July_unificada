---
type: concept
status: active
created: 2026-05-08
updated: 2026-05-08
sources:
  - docs/notion/checklist-web-cliente.md
  - docs/notion/webs-analisis-inicial.md
tags:
  - seo
  - web-cliente
  - astro
---

# SEO local para webs de cliente

SEO basico y local aplicable a webs de cliente, especialmente cuando hay servicios o zonas de trabajo diferenciadas.

## Elementos minimos

- title unico por pagina
- description unica por pagina
- canonical correcto
- Open Graph
- imagen OG real
- schema JSON-LD si aplica
- sitemap
- robots
- alt text en imagenes
- paginas por ciudad o servicio cuando aporte valor

## Patron con Astro

Para webs estaticas con SEO local, Astro permite centralizar datos y generar paginas por ciudad o servicio desde archivos de datos como `locations.ts`.

## Relacionado

- [[Web de cliente para captacion]]
- [[MHK Studio]]
- [[Checklist de entrega de web de cliente]]
