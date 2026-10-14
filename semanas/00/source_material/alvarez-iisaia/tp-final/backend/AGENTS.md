# Instrucciones del backend V2

Aplica a los archivos dentro de `backend/` y a sus tests asociados.

- Mantené engine y sesiones en `db.py`, contratos en `schemas.py`, composición
  en `main.py` y routers/módulos enfocados por dominio.
- `create_app()` admite configuración, SQLite y proveedores inyectables;
  `create_production_app()` es el único punto que carga `.env` y debe fallar si
  faltan sesión o Auth0.
- Toda consulta de cafeterías, visitas, fotos, dashboard y descubrimientos filtra
  por `owner_id`; asociaciones cruzadas devuelven `404`.
- Mutaciones usan `require_csrf`; no debilites `Origin`, cookies,
  `TrustedHostMiddleware` ni encabezados de seguridad.
- No guardes tokens en claro, secretos, refresh tokens, bodies sensibles o
  ubicación actual.
- Places se consume sólo mediante el adaptador inyectable, field masks mínimas y
  sin Geocoding API. Conservá la política de Place ID, TTL y contenido vivo.
- Coordenadas actuales se aceptan sólo en bodies `POST` sin caché y se descartan.
- Uploads: validar contenido, tamaño, dimensiones, animación, propietario y rutas
  generadas por servidor.
- El startup nunca migra una base existente. `status`, `backup`, `upgrade`,
  `verify` y `restore` siguen siendo comandos manuales e idempotentes.
- Los tests usan bases/directorios temporales, Auth/Places falsos y cero red.
