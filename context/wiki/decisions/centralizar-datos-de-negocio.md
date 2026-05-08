---
type: decision
status: active
created: 2026-05-08
updated: 2026-05-08
sources:
  - docs/notion/patron-web-cliente.md
  - docs/notion/webs-analisis-inicial.md
tags:
  - decision
  - web-cliente
  - datos
---

# Centralizar datos de negocio

## Contexto

En las webs de cliente, los datos de negocio aparecen en header, footer, formularios, SEO, structured data, reservas, chatbot, emails y backend.

## Decision

Crear una fuente unica de datos de negocio antes de construir componentes.

## Motivo

Reduce errores al cambiar telefono, email, dominio, horarios, redes, servicios o zonas de trabajo. Tambien evita que al clonar una web queden datos antiguos repartidos por la aplicacion.

## Consecuencias practicas

- Revisar primero donde vive la configuracion del sitio.
- No duplicar contacto manualmente en componentes si se puede importar desde datos.
- En Astro, preferir `src/data/siteConfig.ts`.
- En React/Vite, usar `client/src/content/site.ts` o `shared/business-config.ts`.

## Relacionado

- [[Fuente unica de datos de negocio]]
- [[Web de cliente para captacion]]
- [[Lucy Lara]]
- [[MHK Studio]]
