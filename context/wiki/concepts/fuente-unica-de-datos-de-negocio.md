---
type: concept
status: active
created: 2026-05-08
updated: 2026-05-08
sources:
  - docs/notion/patron-web-cliente.md
  - docs/notion/webs-analisis-inicial.md
tags:
  - web-cliente
  - datos
  - mantenimiento
---

# Fuente unica de datos de negocio

Los datos de identidad y contacto de un cliente deben vivir en un unico sitio y alimentar el resto de la web.

## Datos que centralizar

- nombre comercial
- dominio
- telefono
- email
- direccion
- horarios
- WhatsApp
- redes sociales
- imagen principal
- logo
- servicios
- zonas de trabajo

## Implementacion recomendada

| Stack | Ubicacion sugerida |
| --- | --- |
| Astro | `src/data/siteConfig.ts` |
| React/Vite | `client/src/content/site.ts` o `shared/business-config.ts` |
| HTML estatico | migrar a Astro o crear includes/plantillas |

## Riesgo que evita

Evita que telefono, email, dominio, horarios, URLs, SEO, structured data, chatbot, footer y formularios queden desincronizados.

## Relacionado

- [[Centralizar datos de negocio]]
- [[Web de cliente para captacion]]
- [[Analisis inicial de webs de cliente]]
