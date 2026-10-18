# Evidencia de verificación — Coffee Atlas V3

Fecha de auditoría final: 18 de octubre de 2026.

## Alcance y aislamiento

- Branch auditada: `codex/coffee-atlas-v3`.
- URL canónica: `http://127.0.0.1:8000`.
- Tests ejecutados offline, sin caché de pytest ni bytecode dentro del proyecto.
- Tests de migración ejecutados exclusivamente sobre bases creadas por pytest en
  directorios temporales.
- Navegador ejecutado con SQLite V4, uploads, dos identidades, Places y mapa
  temporales o falsos.
- No se leyó `.env`; sólo se comprobó su presencia.
- No se usaron Auth0, Google ni red. Los tests y el navegador no usaron la base
  ni los uploads reales.
- No se realizó push, merge, rebase, tag ni operación sobre `main`.

La migración y auditoría de la base real se realizaron después mediante
checkpoints expresos, con el servidor detenido. No se ejecutó restore.

## Resultado ejecutivo

- Fallas bloqueantes: **ninguna**.
- Pruebas específicas V3.6: **12 aprobadas**, 0 fallas, 1 warning.
- Pruebas específicas de migración: **11 aprobadas**, 0 fallas, 1 warning.
- Suite completa: **118 aprobadas**, 0 fallas, 1 warning.
- `compileall backend`: correcto.
- `git diff --check`: correcto al cierre documental.
- Navegador: 320, 768 y 1440 px sin overflow horizontal ni errores de consola.

El warning único es conocido y no se oculta:
`AuthlibDeprecationWarning` informa que `authlib.jose` está deprecado y será
compatible sólo antes de Authlib 2.0. La migración a `joserfc` queda como mejora
no bloqueante previa a esa actualización.

## Verificación automática

Pruebas específicas ejecutadas:

```bash
PYTHONDONTWRITEBYTECODE=1 uv run --offline pytest -p no:cacheprovider -q \
  tests/test_frontend_v36.py tests/test_static.py
```

Resultado: `12 passed, 1 warning in 0.38s`.

Suite completa offline:

```bash
PYTHONDONTWRITEBYTECODE=1 \
  uv run --offline pytest -p no:cacheprovider -q
```

Resultado: `118 passed, 1 warning in 4.48s`.

Compilación:

```bash
uv run --offline python -m compileall -q backend
```

Resultado: exit code `0`, sin diagnósticos.

## Dashboard y compatibilidad V2

- La interfaz contiene sólo **Dashboard personal**; el bloque `stats-grid` no
  existe y la carga normal no solicita `getStats()`.
- `GET /api/stats` continúa autenticado, aislado y cubierto por pruebas de
  lectura, escritura y autorización.
- La serie contiene doce meses en orden, incluido cambio de año.
- Cero, una visita, datos dispersos y máximos repetidos están cubiertos.
- Gráfico, resumen y tabla se derivan de la misma serie; la tabla
  conserva mes, visitas y acumulado.
- El navegador mostró escala entera, líneas de referencia, meses identificables
  y alternativa tabular accesible.
- V3.6 omite etiquetas de cero sobre los meses, conserva un único cero de eje,
  usa ticks enteros sin duplicados y evita scroll innecesario en escritorio.

## Orden final y paginación V3.6

- Menú y DOM siguen Descubrir, Mis cafeterías, Mapa y Dashboard.
- Perfil y recomendaciones comparten fila en escritorio y se apilan en móvil.
- El formulario único de filtros está dentro de Mis cafeterías, antes de la
  grilla, sin alterar su comportamiento.
- Las recomendaciones se paginan localmente de a cuatro mediante `slice` sobre
  los resultados ya recibidos.
- Los casos 0, 1, 4, 5 y 19 fueron comprobados; una búsqueda nueva vuelve a la
  página 1 y la paginación se oculta cuando no hace falta.
- Anterior/Siguiente conservan foco útil en los límites y anuncian el cambio por
  una región `aria-live`.
- Cambiar de página no ejecutó llamadas adicionales ni escrituras.

## Barrios de CABA

- `backend/data/caba_neighborhoods.geojson` es un `FeatureCollection` con
  exactamente 48 features y 48 valores `BARRIO` únicos.
- El catálogo derivado contiene 48 nombres únicos y usa la clave de ordenación
  española definida por la aplicación.
- Todas las features tienen correspondencia canónica.
- Aliases seguros cubren mayúsculas, espacios, puntuación y variantes con o sin
  acentos sin reinterpretar valores ambiguos.
- El endpoint devuelve siempre los 48 barrios y separa **Valores históricos**.
- Dos identidades falsas recibieron históricos distintos; no hubo filtración.
- Un valor histórico siguió siendo filtrable y las altas nuevas usaron el
  barrio calculado por el backend.
- Fuente, fecha de incorporación, licencia y SHA-256 local comprobados están en
  `backend/data/README.md`; no se agregaron metadatos supuestos.

## Places, mapa y recomendaciones

- `POST /api/places/{place_id}/prepare-cafe` exige sesión, CSRF y `Origin`.
- Place Details valida coincidencia estricta de ID, forma de respuesta y CABA.
- Proveedor caído, respuesta inválida y ubicación fuera de CABA tienen errores
  seguros probados.
- Preparar no persiste. El guardado final usa `POST /api/cafes` y vuelve a
  validar Details sin confiar en nombre, dirección, barrio o coordenadas del
  navegador.
- Los endpoints V2 `prepare-save` y `save` de recomendaciones permanecen
  compatibles y reutilizan la lógica de preparación.
- El buscador de Places es el recorrido por teclado; los POI son complementarios
  y sólo actúan cuando existe un Place ID.
- Mapa, POI y recomendaciones abrieron el mismo formulario con nombre y
  dirección canónicos precargados.
- No hubo guardado automático: la persistencia ocurrió sólo al confirmar.
- El duplicado propio mostró **Ya está en tu atlas**; el mismo Place ID guardado
  por otra identidad se presentó como alta disponible, sin revelar el dato ajeno.

## Descripción opcional y esquema V4

- Alta con campo omitido, `null`, vacío o espacios produce `NULL`.
- Textos normalizados de 1 y 600 caracteres son válidos; 601 se rechaza.
- `PATCH` agrega, cambia y quita una descripción.
- Lectura y serialización preservan `null`; las tarjetas muestran
  **Sin descripción.** sin hueco visual.
- Mapa y recomendaciones admiten alta sin descripción.

La suite de migración se ejecutó aparte con salida nominal:

```text
11 passed, 1 warning in 0.17s
```

Cubrió exclusivamente en `tmp_path`:

- `status`, backup, upgrade, verify e idempotencia;
- V3→V4 conservando filas, IDs, descripciones, propietarios, Place IDs,
  coordenadas, barrios, timestamps, FKs, índices, unicidad y relaciones;
- `PRAGMA integrity_check` y verificación de esquema;
- rollback completo ante fallo simulado;
- restore reproducible con backup de rescate;
- startup rechazando una V3 pendiente sin modificarla;
- rutas de backup, upgrade y restore contenidas en el directorio temporal.

No se usó una copia de la base real.

## Migración y auditoría de la base real

La operación real se realizó con autorizaciones independientes y el servidor
detenido:

- backup previo conservado en
  `data/backups/coffee-atlas-v3-pre-v4-20261018-000900.db`;
- SHA-256 del backup:
  `799be62172905d5e7921c827bf8b57006896b8ce983ad3302ab72ef5a7848013`;
- migración V3→V4 y `verify` completados;
- no se ejecutó restore.

El estado inmediatamente posterior a la migración fue `94208` bytes, mtime
`2026-10-18T00:43:03-0300`, SHA-256
`f9beb5b86ffa176fd17f3fa8ebd2bc1942339db8da3357d22fd25282176bba92`
y conteos `9/8/4` para cafeterías, visitas y fotografías.

La auditoría final abrió SQLite exclusivamente con `-readonly` y
`PRAGMA query_only=ON`. Registró:

- `94208` bytes, permisos `0644`, mtime `2026-10-18T11:04:58-0300` y SHA-256
  `d5a71aa99080f2b87cc01702d048ba125451640c2411ae69a8a1006db51c9eb6`;
- versiones 2, 3 y 4 registradas una vez cada una; V4 es la actual;
- `cafes.description` con `notnull=0`;
- `integrity_check=ok` y cero filas en `foreign_key_check`;
- conteos actuales `10/8/4`;
- tablas `cafes`, `migration_imports`, `place_discoveries`,
  `schema_migrations`, `sessions`, `users`, `visit_photos` y `visits`;
- unicidades históricas y los índices explícitos de `visit_photos` conservados;
- ausencia de `-wal`, `-shm`, `-journal`, `.restoring` y `.before-restore`.

Tamaño, mtime y SHA-256 resultaron idénticos antes y después de la auditoría.
Frente al estado posmigración, el tamaño y el esquema permanecen iguales, las
visitas y fotografías no cambiaron y existe una cafetería adicional. Esos datos
no permiten atribuir el cambio a una acción o identidad: **causa no demostrable**.

## Seguridad y privacidad

- Consultas y mutaciones personales filtran por `owner_id`; los IDs ajenos
  devuelven `404`.
- Mutaciones conservan CSRF y comparación exacta del `Origin` canónico.
- Sesiones guardan hashes y usan cookie `HttpOnly`, `SameSite=Lax`, host-only y
  `Secure` fuera de desarrollo.
- `TrustedHostMiddleware` deriva el host permitido de la URL canónica.
- CSP, `X-Content-Type-Options: nosniff`, `Referrer-Policy` y
  `X-Frame-Options: DENY` siguen presentes.
- Fotos se sirven por endpoint autenticado con `Cache-Control: private,
  no-store`.
- Ubicación actual ausente de URL, SQLite y storage del navegador.
- `frontend/js/api.js` sigue siendo la única capa con `fetch`.
- No se detectaron secretos, claves privadas, bases, backups o uploads
  versionados.

## Dependencias y archivos versionados

- Dependencias de producto declaradas únicamente en `pyproject.toml` y
  resueltas en `uv.lock`.
- No se agregaron dependencias de frontend, Node, React, JSX/TSX, Tailwind,
  shadcn, `package.json`, lockfiles de Node, `components.json`, `.21st/` ni
  `node_modules`.
- No hay recursos remotos nuevos en HTML o CSS; Google Maps continúa siendo el
  único script remoto construido por el módulo autorizado.
- No hay symlinks de producto; los únicos hallados pertenecen a `.venv`, que
  está ignorado.
- Ningún archivo ignorado está versionado.
- `.gitignore` cubre `.env`, bases SQLite, uploads, caches Python y pytest.

## Sistema visual y accesibilidad

- Las 34 variables CSS referenciadas están definidas; no existen referencias a
  variables faltantes.
- No se usa `overflow-x: hidden`.
- Existe `prefers-reduced-motion: reduce` y las transiciones son breves y
  funcionales.
- Contrastes calculados para pares principales: tinta/canvas `16.18:1`, texto
  secundario/canvas `6.99:1`, texto claro/terracota `7.13:1`, texto claro/oliva
  `8.03:1` y texto claro/destructivo `8.12:1`.
- Enlace para saltar al contenido: `Tab` lo enfocó y `Enter` trasladó foco a
  `main#main-content`.
- Labels, headings, `aria-live`, `aria-busy`, foco doble y retorno de foco se
  conservaron.
- Los controles propios visibles midieron al menos 44×44 px. Los controles
  mínimos detectados durante la auditoría pertenecían sólo al adaptador falso
  temporal, no al producto.

## Navegador temporal

El detalle reproducible está en `docs/browser-checklist-v3.md`.

Resultados medidos:

| Viewport | Dashboard | Colección | Mapa | `scrollWidth` |
|---|---|---|---|---|
| 320 × 900 | KPI 2×2 | 1 columna | apilado | 320 |
| 768 × 900 | KPI 2×2 | 2 columnas | apilado | 768 |
| 1440 × 1000 | KPI 4×1 | 3 columnas | composición 4/8 | 1440 |

El ancho principal a 1440 fue `1180 px`. No hubo overflow ni errores o warnings
de la aplicación en consola. También se comprobaron:

- buscador mediante teclado, selección POI y acción explícita;
- precarga canónica y alta sin descripción;
- duplicado propio y aislamiento entre dos identidades;
- recomendación, cancelación y restauración de foco;
- historial con nota y fotografía temporal servida como `image/jpeg`;
- estados de carga, vacío, error/degradado y confirmación;
- Términos y Privacidad a 320 px sin overflow;
- modo degradado con mensajes diferenciados para mapa, alta y domicilio.

Las interacciones POI, cancelación y retorno de foco son evidencia de navegador,
no tests E2E persistentes. No se agregó Node ni una infraestructura E2E.

## Skills de revisión

- **UI/UX Pro Max:** se aplicaron localmente sus criterios de accesibilidad,
  dashboard, gráficos, formularios, foco y responsive. No se ejecutó red.
- **21st UI Review:** se usó sólo como checklist textual de jerarquía,
  consistencia, estados y responsive. No se usaron CLI, MCP, cuentas, API keys,
  `21st review`, `--fix`, `npx`, React, shadcn ni servicios remotos.
- **preentrega-coffee-atlas:** se aplicó como checklist conservador. Aunque su
  nombre refiera a V2, sus controles de Git, seguridad, tests, migraciones,
  navegador y documentación siguen siendo aplicables; se ajustaron el esquema,
  los documentos y los criterios al contrato V3.

## Mejoras no bloqueantes y límites

- Migrar `authlib.jose` a `joserfc` antes de Authlib 2.0.
- La accesibilidad de los POI nativos depende de Google; el buscador accesible
  permanece como recorrido principal y completo.
- Auth0 y Google reales conservan sus checkpoints separados; no se repitieron.
- Cualquier operación real futura —incluido restore— conserva el requisito de
  autorización específica y servidor detenido.
- SQLite y uploads continúan siendo almacenamiento local sin replicación.

## Documentos históricos

`docs/spec.md`, `docs/plan.md`, `docs/spec-v2.md`, `docs/plan-v2.md`,
`docs/verification-v2.md` y `docs/browser-checklist-v2.md` permanecen intactos.
