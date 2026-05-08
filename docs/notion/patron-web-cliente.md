# Patron: Web de cliente para captacion

## Cuándo usarlo

Usar este patron para webs de negocios locales, marcas personales, estudios profesionales, terapeutas, centros de estetica, interioristas, consultores o servicios similares.

## Objetivo

Convertir visitantes en contactos reales: llamada, WhatsApp, formulario, reserva o email.

## Estructura recomendada

1. Hero con propuesta clara
2. Servicios principales
3. Diferenciador o metodo de trabajo
4. Prueba social, marcas, testimonios o casos
5. SEO por servicio o ubicacion si aplica
6. CTA visible varias veces
7. Pagina de contacto
8. Legal minimo

## Fuente unica de datos

Antes de construir componentes, definir:

- Nombre comercial
- Dominio
- Telefono
- Email
- Direccion
- Horarios
- WhatsApp
- Redes sociales
- Imagen principal
- Logo
- Servicios
- Zonas de trabajo

## Stack recomendado

### Web estatica o SEO local

- Astro
- Tailwind
- `siteConfig`
- paginas generadas desde datos
- Render/Vercel/Netlify

### Web con app, reserva, backend o IA

- React + Vite o Next.js
- Backend Express o API routes
- Supabase si hay persistencia o conocimiento dinamico
- OpenAI solo si el chatbot aporta valor

## Reglas de Sergio

- No clonar una web cambiando solo colores y logo.
- Centralizar identidad y contacto.
- Confirmar envio real de formularios.
- Revisar mobile antes de entregar.
- Revisar SEO pagina por pagina.
- Si hay Supabase en produccion, usar pooler para la conexion.
- No exponer claves privadas en frontend.

