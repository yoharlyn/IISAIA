# Evidencia de verificación — Coffee Atlas V2

Fecha de cierre: 14 de octubre de 2026.

## Entorno y aislamiento

- Branch: `codex/coffee-atlas-v2`.
- URL canónica: `http://127.0.0.1:8000`.
- Tests ejecutados offline con caché en `/private/tmp`.
- SQLite, uploads, Auth0 y Places falsos en pruebas y navegador final.
- Sin lectura de `.env`, consumo de cuota, push ni cambios en datos reales.
- La base real conservó antes y después el tamaño, mtime y SHA-256 registrados
  en el checkpoint.

## Verificación automática

```bash
UV_CACHE_DIR=/private/tmp/coffee-atlas-uv-cache uv run --offline pytest -q
UV_CACHE_DIR=/private/tmp/coffee-atlas-uv-cache uv run --offline python -m compileall -q backend
git diff --check
```

Resultado actual:

- 91 tests aprobados y 0 fallas.
- 1 warning: `AuthlibDeprecationWarning` por `authlib.jose`; conocido y no
  ocultado.
- `compileall` y `git diff --check`: correctos.

La suite cubre sesiones, CSRF, expiraciones, Auth0 falso, dos usuarios,
aislamiento, migraciones temporales, CABA, TTL, Haversine, Places falso,
recomendaciones, visitas, fotos, dashboard, rutas estáticas, hosts y encabezados
de seguridad. Toda salida de red queda sustituida por dobles.

## Navegador temporal

- 320 px: sin overflow y todos los controles dentro del viewport.
- 768 px: grillas de dos columnas sin overflow.
- 1440 px: grilla de cafeterías de tres columnas sin overflow.
- Diálogo: foco entra en el primer campo y `Escape` lo devuelve al disparador.
- Dashboard: gráficos con tablas equivalentes.
- Fallback **Sin fotografía** visible.
- Modo degradado de mapa y autocompletado comprensible.
- Nearby falso: dos recomendaciones con procedencia y atribución separadas.
- Segunda identidad: atlas vacío, total cero y sin datos de la propietaria.
- Términos y Privacidad: 320/1440 px, semántica, teclado y sin overflow.
- Consola: cero errores y cero advertencias de la aplicación.

## Seguridad revisada

- Host derivado de la URL canónica y `localhost` rechazado.
- CSP limitada a la aplicación, imágenes permitidas por el contrato y orígenes
  necesarios de Google Maps.
- `X-Content-Type-Options`, `Referrer-Policy`, `X-Frame-Options` y
  `frame-ancestors` presentes.
- Factory real fail-closed ante sesión/Auth0 faltantes.
- Secretos ausentes del frontend y respuestas públicas.
- Ubicación actual ausente de URLs, SQLite y storage persistente.
- Fotos privadas protegidas por autenticación, propietario y validación de
  contenido.

## Checkpoints reales anteriores

- Auth0: login, callback, reconciliación del propietario, acceso a siete
  cafeterías, CSRF, sesión y logout verificados en su checkpoint manual.
- Google: mapa, Autocomplete, Place Details, Nearby, CABA, atribución y errores
  verificados tras el checkpoint manual de Google Cloud.
- Regresión de domicilio: una selección real con una variante textual distinta
  se guardó correctamente usando la dirección canónica devuelta por Place
  Details. La evidencia fue sanitizada y no conserva correo, domicilio, Place ID
  ni otros datos personales.
- Migraciones: V1 y ampliación geográfica tuvieron backups independientes,
  integridad, upgrade, verify y status aceptados en sus checkpoints.

Estas verificaciones no se repitieron durante el cierre porque requerían
recursos o datos reales fuera de la autorización de Fase 5.

## Documentos históricos

`docs/spec.md`, `docs/plan.md`, `docs/spec-v2.md` y `docs/plan-v2.md` permanecen
sin modificaciones retroactivas. Las diferencias de ejecución están explicadas
en el README.
