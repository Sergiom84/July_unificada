---
type: source
status: active
created: 2026-05-08
updated: 2026-05-08
sources:
  - docs/notion/patron-web-cliente.md
tags:
  - web-cliente
  - captacion
  - patron
---

# Patron web de cliente para captacion

## Resumen

Documento curado que define cuando usar el patron de web de cliente para captacion, su objetivo, estructura recomendada, fuente unica de datos, stack recomendado y reglas practicas de Sergio.

## Ideas principales

- El objetivo central es convertir visitantes en contactos reales.
- Antes de construir hay que definir datos de negocio: nombre, dominio, telefono, email, direccion, horarios, WhatsApp, redes, imagenes, logo, servicios y zonas.
- Las webs estaticas o SEO local encajan bien con Astro, Tailwind, `siteConfig` y paginas generadas desde datos.
- Las webs con app, reserva, backend o IA pueden necesitar React/Vite o Next.js, backend y Supabase.
- No se debe clonar una web cambiando solo colores y logo.
- Los formularios deben probar envio real.
- La IA solo debe entrar cuando aporte valor.

## Conceptos relacionados

- [[Web de cliente para captacion]]
- [[Fuente unica de datos de negocio]]
- [[Formularios con envio real]]
- [[SEO local para webs de cliente]]
- [[Usar IA solo cuando aporta]]

## Fuente

- `docs/notion/patron-web-cliente.md`
