---
type: decision
status: active
created: 2026-05-08
updated: 2026-05-08
sources:
  - docs/notion/checklist-web-cliente.md
  - docs/notion/webs-analisis-inicial.md
tags:
  - decision
  - formularios
  - deploy
---

# Validar formularios en deploy

## Contexto

Los formularios pueden funcionar visualmente en local y aun asi no enviar nada en produccion. En los proyectos analizados aparece como riesgo recurrente.

## Decision

Ningun formulario se considera terminado hasta probar envio real en el entorno de deploy.

## Motivo

El valor de una web de captacion depende de que las solicitudes lleguen. Un formulario falso o mal integrado rompe el objetivo principal de la web.

## Consecuencias practicas

- Probar envio real en el dominio o entorno desplegado.
- Confirmar recepcion por email, base de datos o herramienta correspondiente.
- Verificar mensaje de exito y mensaje de error.
- Revisar privacidad y anti-spam si aplica.
- Confirmar que la plataforma de formularios coincide con el hosting real.

## Relacionado

- [[Formularios con envio real]]
- [[Checklist de entrega de web de cliente]]
- [[Zaidy]]
- [[MHK Studio]]
