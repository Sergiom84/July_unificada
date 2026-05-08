---
type: concept
status: active
created: 2026-05-08
updated: 2026-05-08
sources:
  - docs/notion/checklist-web-cliente.md
  - docs/notion/webs-analisis-inicial.md
tags:
  - formularios
  - deploy
  - web-cliente
---

# Formularios con envio real

Los formularios son un riesgo recurrente porque pueden parecer terminados aunque no envien datos en produccion.

## Criterio de terminado

Un formulario no se da por terminado hasta probar envio real en el entorno de deploy.

## Checklist minimo

- validacion frontend
- envio real probado
- mensaje de exito
- mensaje de error
- email o almacenamiento confirmado
- checkbox de privacidad si aplica
- prueba en entorno de deploy
- proteccion anti-spam si aplica

## Riesgos detectados

- Formulario que valida y muestra exito pero no envia.
- Formulario configurado para una plataforma distinta al deploy real.
- Contrato frontend/backend desincronizado.

## Relacionado

- [[Validar formularios en deploy]]
- [[Checklist de entrega de web de cliente]]
- [[Analisis inicial de webs de cliente]]
