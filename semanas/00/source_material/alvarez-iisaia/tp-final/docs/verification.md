# Evidencia de verificación

Fecha local: 2026-10-13  
Branch: `codex/coffee-atlas-mvp`

## Pruebas automatizadas

```text
uv run pytest -q
25 passed in 0.36s
```

La suite usa archivos SQLite temporales y cubre:

- seed inicial, segundo arranque y eliminación no restaurada;
- listado, detalle, orden, búsqueda parcial case-insensitive y comodines
  literales;
- filtros individuales y combinados;
- estadísticas globales;
- creación, normalización y validaciones 422;
- `PATCH` parcial, valores nulos permitidos, favorito y timestamps;
- `DELETE` con body vacío y 404 de dominio;
- persistencia entre dos instancias de FastAPI;
- entrega de HTML, CSS, módulos y documentación de FastAPI.

## Verificación HTTP real

Con FastAPI en `127.0.0.1:8000`:

- `GET /api/stats` → `200` y `7/4/3/3`.
- `GET /api/cafes?q=Bruma&is_favorite=true` → `200`, sólo Bruma Café.
- `GET /` → `200 text/html`.
- `GET /css/styles.css` → `200 text/css`.
- `DELETE /api/cafes/8` sobre el registro temporal → `204`.

## Navegador

La verificación se ejecutó con el navegador integrado y locators de Playwright.

- 320 px: una columna; viewport y ancho de documento de 320 px.
- 768 px: dos columnas.
- 1440 px: tres columnas.
- Siete tarjetas y contadores iniciales correctos.
- Búsqueda “Bruma” combinada con favoritas: un resultado.
- Alta de Prisma Café con cuatro ratings y URL deliberadamente rota.
- Fallback “Sin fotografía” visible.
- Edición a “Prisma Café Editado” y cambio a `PENDING`.
- Favorito quitado con actualización de estadísticas.
- Diálogo de eliminación abierto y cancelado; la tarjeta permaneció y el foco
  volvió al botón “Eliminar”.
- Formulario cerrado con Escape; el foco volvió a “Agregar cafetería”.
- Tras reiniciar FastAPI, Prisma Café Editado y los contadores 8/4/4/3 seguían
  presentes, demostrando persistencia.
- El registro temporal se eliminó por API y la interfaz volvió al seed de siete.
- Con FastAPI detenido, “Aplicar filtros” mostró el mensaje de conexión y el
  botón “Reintentar”. Después de reiniciar, ese botón recuperó las siete tarjetas
  y volvió a ocultarse.
- Consola final: sin warnings ni errores.

## Resultado

No se encontraron defectos funcionales durante el recorrido. La confirmación
destructiva final desde el botón queda documentada como comprobación manual
opcional; el contrato y la persistencia de la eliminación están automatizados.
