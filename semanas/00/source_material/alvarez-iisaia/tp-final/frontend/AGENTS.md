# Instrucciones del frontend V2

Aplica a los archivos dentro de `frontend/` y a la verificación en navegador.

- Usá HTML semántico, un único CSS y módulos ES nativos. No agregues Node,
  bundlers, frameworks ni dependencias de CDN para la lógica de la aplicación.
- `api.js` es la única capa que llama a `fetch`, agrega CSRF y traduce errores.
- Construí contenido remoto con `createElement`, atributos y `textContent`; no
  interpoles datos con `innerHTML`.
- La ubicación actual vive sólo en memoria. No uses query strings,
  `localStorage`, `sessionStorage` ni IndexedDB.
- Mapa y autocomplete ofrecen estados degradados claros. No ocultes atribuciones
  de Google Maps y separá contenido Google, cálculos personales y datos locales.
- Cada operación asíncrona muestra carga, éxito o error. Deshabilitá el botón de
  envío mientras haya una mutación en curso.
- Conservá labels visibles, foco perceptible, orden natural, `aria-live`, retorno
  de foco y alternativas tabulares para gráficos.
- Nada depende sólo del color. Verificá 320, 768 y 1440 px sin overflow y consola
  limpia.
- Términos y Privacidad son páginas locales, accesibles y sin afirmaciones
  legales inventadas.
