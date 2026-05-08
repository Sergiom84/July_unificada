# Analisis inicial de webs de cliente

## Objetivo

Detectar patrones comunes entre webs ya hechas y una web en progreso para convertirlos en memoria reutilizable de Sergio.

## Proyectos revisados

### Lucy Lara

- Ruta local: `C:\Users\sergi\Desktop\Aplicaciones\Lucy-lara-site`
- Repo: `git@github.com:Sergiom84/lucy-lara-site`
- Estado: finalizada, con cambios locales pendientes
- Stack: React 18, TypeScript, Vite, Tailwind, Wouter, Express, Drizzle, OpenAI, Supabase RPC para conocimiento del chatbot, Render
- Tipo de web: negocio local de estetica con captacion, catalogo, reserva, chatbot y contenido SEO por servicios

Puntos fuertes:

- Tiene `AGENTS.md`, que ya funciona como contexto canonico para agentes.
- Arquitectura potente para negocio local con catalogo, booking, chatbot y backend.
- Hay conocimiento tecnico documentado: Google Maps, formularios, pasarela de pagos, Render, OpenAI, seguridad.
- Tiene pipeline de conocimiento para chatbot.

Riesgos reutilizables:

- Datos de negocio repetidos en muchas capas: header, footer, booking, productos, structured data, email, chatbot y backend.
- Formulario de reserva y backend pueden desincronizarse.
- Persistencia real no queda clara: existen Drizzle/DATABASE_URL, pero el runtime usa memoria segun `AGENTS.md`.
- Endpoints admin sin autenticacion segun `AGENTS.md`.
- Al clonar, no basta con cambiar colores y logo: hay que barrer dominio, email, telefono, horarios, URLs, CSP, SEO, chatbot y correo.

Nota para Notion:

> Lucy Lara debe guardarse como "plantilla avanzada para negocio local con IA/chatbot", pero antes de reutilizarla conviene centralizar datos de negocio y simplificar contratos.

### Zaidy

- Repo: `https://github.com/Sergiom84/Zaidy`
- Estado: finalizada
- Stack: HTML, CSS, JavaScript, Playwright como devDependency, Render static
- Tipo de web: marca personal/coaching con blog, tienda, recursos, contacto y lead magnet

Puntos fuertes:

- Estructura muy simple: HTML estatico, CSS global y JS unico.
- Buen enfoque de paginas comerciales: inicio, servicios, medios, blog, tienda, contacto, privacidad.
- Lead magnet con modal, validacion y preparacion para email marketing.
- README contiene checklist de publicacion y SEO.

Riesgos reutilizables:

- Mucha repeticion entre paginas HTML.
- El formulario de contacto valida y muestra exito, pero no envia datos realmente.
- SEO completo en home, pero el propio README avisa que faltan metatags en otras paginas.
- Integraciones de email, handbook y analytics quedaron como tareas pendientes.

Nota para Notion:

> Zaidy debe guardarse como "plantilla estatica rapida para marca personal", util cuando el cliente necesita presencia, contenidos y lead magnet, pero sin backend real.

### MHK Studio

- Ruta local: `C:\Users\sergi\Desktop\Aplicaciones\Marta Harranz\Mhkstudio`
- Repo: `git@github.com:Sergiom84/MHKstudio.git`
- Estado: en desarrollo
- Stack: Astro 6, Tailwind 4, sitemap, Render static
- Tipo de web: estudio de interiorismo con SEO local por ciudades

Puntos fuertes:

- `siteConfig` centraliza nombre, descripcion, URL, telefono, email, direccion y redes.
- `locations.ts` permite crear paginas SEO por ciudad con `getStaticPaths`.
- `Layout.astro` concentra metadatos, Open Graph, Twitter Card y schema sitewide.
- Formulario de contacto sencillo con Netlify Forms.
- Muy buena base para webs de cliente estaticas con SEO local.

Riesgos o decisiones pendientes:

- README sigue siendo el starter de Astro; falta documentar el proyecto real.
- Formulario usa `data-netlify`, pero el deploy actual esta en Render. Confirmar si Render gestionara formularios o si hay que usar otra solucion.
- Revisar si la ruta rewrite de Render para SPA es adecuada para sitio Astro estatico multipagina; puede interferir con paginas generadas si no se sirve como static correcto.
- No hay `AGENTS.md`; conviene crearlo ya para fijar reglas del proyecto.

Nota para Notion:

> MHK Studio debe guardarse como "plantilla moderna para web estatica SEO local", especialmente para negocios con varias zonas de servicio.

## Patrones comunes detectados

### 1. Webs orientadas a captacion

Todas priorizan que el visitante contacte, reserve, escriba por WhatsApp o deje email.

Patron reutilizable:

- Hero con propuesta clara
- Servicios principales
- Prueba social o confianza
- CTA repetido
- Contacto/WhatsApp visible
- Legal minimo

### 2. Identidad y contacto como fuente critica

Telefono, email, direccion, dominio y redes aparecen en muchos sitios.

Regla de Sergio:

> En cualquier web de cliente, crear una fuente unica de datos de negocio antes de construir componentes.

Implementacion recomendada:

- Astro: `src/data/siteConfig.ts`
- React/Vite: `client/src/content/site.ts` o `shared/business-config.ts`
- HTML estatico: considerar migrar a Astro o generar includes/plantillas

### 3. SEO basico siempre necesario

Las tres webs trabajan SEO: metatags, schema, canonical, paginas por servicio o ciudad.

Checklist reutilizable:

- Title unico por pagina
- Description unica
- Canonical correcto
- Open Graph
- Imagen OG real
- Schema JSON-LD
- Sitemap
- Robots
- Alt text en imagenes
- Paginas legales

### 4. Formularios: riesgo frecuente

En Zaidy el formulario no envia; en MHK usa Netlify aunque el deploy es Render; en Lucy hay contrato entre frontend y backend.

Regla de Sergio:

> Ningun formulario se da por terminado hasta probar envio real en entorno de deploy.

Checklist minimo:

- Validacion frontend
- Envio real
- Mensaje de exito/error
- Email o almacenamiento confirmado
- Proteccion anti-spam si aplica
- Politica de privacidad aceptada

### 5. Deploy en Render

Lucy y MHK tienen `render.yaml`; Zaidy tambien.

Patron reutilizable:

- Guardar siempre configuracion de deploy en repo.
- Documentar comandos reales.
- Probar `npm run build` antes de subir.
- Confirmar rutas y cache headers.

### 6. IA/chatbot solo cuando aporta

Lucy incorpora chatbot con OpenAI y Supabase. Zaidy y MHK no lo necesitan de inicio.

Regla de Sergio:

> No meter IA por defecto. Usarla cuando mejore captacion, soporte o consulta de catalogo.

Cuando haya chatbot:

- Definir fuente de conocimiento
- Separar prompt de datos de negocio
- Registrar problemas y soluciones
- Validar respuestas contra datos reales
- Si se usa Supabase, recordar pooler en produccion

## Primeras notas para Notion

Crear estas paginas:

1. `Patron: Web de cliente para captacion`
2. `Checklist: Entrega de web de cliente`
3. `Decision: Centralizar datos de negocio`
4. `Patron: SEO local por ciudad con Astro`
5. `Riesgo: Formularios que parecen funcionar pero no envian`
6. `Patron: Chatbot con conocimiento controlado`
7. `Proyecto: Lucy Lara`
8. `Proyecto: Zaidy`
9. `Proyecto: MHK Studio`

