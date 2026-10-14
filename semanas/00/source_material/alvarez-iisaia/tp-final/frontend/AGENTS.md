# Instrucciones del frontend

Aplica a los archivos dentro de `frontend/` y a la verificación en navegador.

- Usá HTML5 semántico, un único CSS y módulos ES nativos. No agregues Node,
  bundlers, frameworks ni dependencias de CDN para la lógica de la aplicación.
- `api.js` es la única capa que llama a `fetch` y traduce errores HTTP.
- `ui.js` construye contenido con `createElement`, atributos y `textContent`;
  no interpoles datos remotos con `innerHTML`.
- `app.js` coordina estado, filtros, diálogos y recargas sin duplicar reglas del
  backend.
- Cada operación asíncrona muestra carga, éxito o error. Deshabilitá el botón de
  envío mientras haya una mutación en curso.
- Conservá labels visibles, foco con contraste, orden de tabulación natural,
  regiones `aria-live` y retorno de foco al cerrar diálogos.
- No uses emojis como iconos o etiquetas. Todo botón debe comunicar su acción
  mediante texto accesible.
- Las imágenes llevan dimensiones reservadas, carga diferida y fallback local
  cuando la URL está vacía o falla.
- Verificá 320, 768 y 1440 px, recorrido sólo con teclado, consola del navegador
  y todos los estados descritos en `docs/spec.md`.

