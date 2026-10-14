# Instrucciones del backend

Aplica a los archivos dentro de `backend/` y a sus tests asociados.

- Mantené una sola tabla `cafes` y los seis endpoints definidos en
  `docs/spec.md`.
- Separá responsabilidades: engine y sesión en `db.py`, tabla en `models.py`,
  contratos Pydantic en `schemas.py`, seed en `seed.py`, rutas en `routes.py` y
  composición de la aplicación en `main.py`.
- `create_app()` debe admitir una URL SQLite temporal y la opción de ejecutar el
  seed para que los tests no dependan de estado global.
- Abrí una sesión SQLModel por request. Cada mutación debe confirmar la
  transacción y refrescar el modelo antes de responder.
- Normalizá strings en los schemas, prohibí campos extra y conservá `null` sólo
  para `image_url` y ratings.
- Expresá los rangos y valores críticos tanto en la validación como en
  restricciones SQLite cuando sea posible.
- Serializá `created_at` y `updated_at` como UTC explícito.
- El seed sólo corre si la tabla completa está vacía; no debe reponer registros
  eliminados por el usuario.
- La búsqueda escapa `%` y `_`; todos los filtros se combinan con `AND`.
- Cubrí primero el contrato observable: códigos, JSON, persistencia, orden y
  errores. No pruebes detalles internos sin impacto externo.

