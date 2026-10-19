# Coffee Atlas V3

Coffee Atlas es un atlas y diario personal de cafeterías de CABA desarrollado
con FastAPI, SQLModel, SQLite y un frontend HTML, CSS y JavaScript vanilla. V3
unifica el alta desde Google Places, consolida el catálogo oficial de barrios,
admite descripciones opcionales y renueva el dashboard y el sistema visual sin
agregar frameworks ni dependencias de frontend. El recorrido final presenta
Descubrir, Mis cafeterías, Mapa y Dashboard en ese orden.

La especificación vigente está en [`docs/spec-v3.md`](docs/spec-v3.md) y el
orden aprobado en [`docs/plan-v3.md`](docs/plan-v3.md). Los documentos V1 y V2
permanecen congelados como registro histórico.

## Funcionalidades

- Login y registro mediante Auth0 Universal Login.
- Sesiones locales opacas; SQLite conserva sólo el hash del token.
- Cafeterías, visitas, fotos, dashboard y recomendaciones aislados por persona.
- Un único dashboard con gráfico SVG de doce meses, resumen y tabla accesible.
- Filtros integrados en **Mis cafeterías**, antes de la colección.
- Catálogo derivado del GeoJSON versionado con los 48 barrios oficiales de CABA.
- Valores históricos de barrio separados, filtrables y privados por propietario.
- Buscador accesible de Places junto al mapa y selección complementaria de POI.
- Preparación canónica de nombre, dirección y barrio mediante Place Details.
- Formulario compartido por alta general, mapa, POI y recomendaciones.
- Duplicados por propietario y Place ID, sin revelar datos de otras personas.
- Descripción opcional persistida como `NULL` o texto de 1 a 600 caracteres.
- Historial de visitas con cuatro valoraciones y hasta cinco fotos privadas.
- Recomendaciones determinísticas con atribución y persistencia mínima.
- Recomendaciones paginadas localmente de a cuatro, sin nuevas llamadas al
  proveedor al cambiar de página.
- Interfaz responsive con foco visible, reducción de movimiento y modo degradado.
- Páginas locales de Términos y Privacidad.

`GET /api/stats` y los endpoints V2 de recomendaciones se conservan como
contratos compatibles aunque la interfaz V3 use `/api/dashboard`, la preparación
genérica y `POST /api/cafes`.

## Requisitos

- Python 3.11 o superior.
- [uv](https://docs.astral.sh/uv/).
- Una aplicación Auth0 de tipo **Regular Web Application**.
- Maps JavaScript API y Places API (New) habilitadas en Google Cloud.

No se utiliza Geocoding API, Node, bundler, framework frontend, librería de
gráficos, Docker ni Alembic.

## Instalación y configuración local

El único origen soportado es `http://127.0.0.1:8000`. No usar `localhost`: es
otro host para cookies, callbacks y validación de `Origin`.

```bash
uv sync
cp .env.example .env
```

Completar `.env` localmente sin versionarlo. Variables disponibles, sin valores:

```text
APP_BASE_URL
APP_ENV
SESSION_SECRET
AUTH0_DOMAIN
AUTH0_CLIENT_ID
AUTH0_CLIENT_SECRET
AUTH0_CALLBACK_URL
AUTH0_LOGOUT_RETURN_URL
LEGACY_OWNER_AUTH0_SUB
GOOGLE_MAPS_BROWSER_KEY
GOOGLE_MAPS_SERVER_KEY
GOOGLE_MAP_ID
DATABASE_URL
UPLOAD_DIR
```

Configuración Auth0:

```text
Callback:    http://127.0.0.1:8000/auth/callback
Logout:      http://127.0.0.1:8000/
Web origin:  http://127.0.0.1:8000
```

La clave Google del navegador debe aceptar `http://127.0.0.1:8000/*`. Habilitar
solamente Maps JavaScript API y Places API (New), restringir cada clave por API y
configurar presupuesto y alertas. La clave web es visible en el navegador; la
clave servidor, los secretos Auth0 y `SESSION_SECRET` nunca se envían al frontend.

No pegar secretos en chats, logs, capturas ni documentación.

## Ejecución

```bash
uv run fastapi dev backend/main.py \
  --factory \
  --host 127.0.0.1 \
  --port 8000 \
  --no-access-log
```

Abrir `http://127.0.0.1:8000`. La factory real carga `.env` y falla de forma
segura si faltan la clave de sesión o las variables Auth0 requeridas.

## Esquema V4 y migraciones manuales

El esquema objetivo es V4. Su única diferencia estructural respecto de V3 es
que `cafes.description` admite `NULL`; la migración conserva filas, IDs,
propietarios, Place IDs, coordenadas, barrios, timestamps, índices, constraints
y relaciones con visitas y fotografías.

El startup nunca migra una base existente. Una base V3 pendiente es rechazada
sin escrituras hasta completar el procedimiento manual. Ejecutar siempre con el
servidor detenido, rutas explícitas previamente comprobadas y autorización para
la base objetivo:

```bash
uv run python -m backend.migrations status \
  --database /ruta/explicita/coffee_atlas.db

uv run python -m backend.migrations backup \
  --database /ruta/explicita/coffee_atlas.db \
  --output /ruta/explicita/backups/coffee-atlas-AAAA-MM-DD-HHMMSS.db

uv run python -m backend.migrations upgrade \
  --database /ruta/explicita/coffee_atlas.db \
  --backup /ruta/explicita/backups/coffee-atlas-AAAA-MM-DD-HHMMSS.db

uv run python -m backend.migrations verify \
  --database /ruta/explicita/coffee_atlas.db
```

El backup se crea antes del upgrade. `verify` ejecuta el control de integridad y
comprueba el esquema actual. Repetir `status` y `verify` después de la operación.
No reintentar ni restaurar automáticamente ante un fallo.

Rollback manual, también con servidor detenido y autorización independiente:

```bash
uv run python -m backend.migrations restore \
  --database /ruta/explicita/coffee_atlas.db \
  --from /ruta/explicita/backups/coffee-atlas-AAAA-MM-DD-HHMMSS.db
```

`restore` valida la fuente y crea un backup de rescate con sufijo
`.before-restore` antes de reemplazar el destino. SQLite y `data/uploads/` deben
respaldarse y recuperarse como una unidad coherente.

La migración real V3→V4 se ejecutó posteriormente bajo autorizaciones separadas,
con el servidor detenido y después de validar el backup previo conservado en
`data/backups/coffee-atlas-v3-pre-v4-20261018-000900.db`. La auditoría final de
sólo lectura confirmó V4, `cafes.description` nullable, integridad correcta y
cero violaciones de claves foráneas. No se ejecutó un restore.

## Pruebas

```bash
uv run --offline pytest -p no:cacheprovider -q
uv run --offline python -m compileall -q backend

git diff --check
```

La suite final contiene **118 tests aprobados**; los 12 tests específicos de
V3.6 también pasan. La única advertencia conocida es la deprecación de
`authlib.jose` detallada más abajo.

Los tests bloquean la red y usan SQLite, uploads, identidades y Places
temporales o falsos. La evidencia final está en
[`docs/verification-v3.md`](docs/verification-v3.md) y el recorrido visual en
[`docs/browser-checklist-v3.md`](docs/browser-checklist-v3.md).

## Arquitectura y estructura

```text
Auth0 Universal Login
        | OIDC Authorization Code
        v
FastAPI -- sesión local opaca -- SQLite (esquema V4)
   |                              |- users / sessions
   |                              |- cafes / visits / visit_photos
   |                              `- place_discoveries
   |- Places API (New)
   |- GeoJSON versionado de CABA
   |- data/uploads/ privado
   `- frontend HTML/CSS/JS
          |- Maps JavaScript API
          `- navigator.geolocation efímera
```

- `backend/`: autenticación, configuración, migraciones, Places, geografía,
  cafeterías, visitas, uploads, dashboard y recomendaciones.
- `backend/data/`: perímetro y barrios de CABA, fuente y licencia comprobadas.
- `frontend/`: shell, estilos y módulos ES sin proceso de build.
- `tests/`: pruebas unitarias e integración con recursos temporales.
- `docs/`: especificaciones, planes, checklists y evidencia por versión.
- `.codex/skills/`: referencias UX locales y sus licencias.

Los routers `/auth` y `/api` se registran antes del frontend estático.
`frontend/js/api.js` es la única capa HTTP del navegador y el contenido dinámico
se construye con APIs seguras del DOM.

## API principal

- `/auth/login`, `/auth/signup`, `/auth/callback` y `POST /auth/logout`.
- `/api/session`, `/api/config`, `/api/profile` y `/api/neighborhoods`.
- CRUD `/api/cafes`, `POST /api/cafes/search` y `GET /api/stats` compatible.
- `POST /api/places/{place_id}/prepare-cafe`.
- Visitas bajo `/api/cafes/{id}/visits` y `/api/visits/{id}`.
- Fotos bajo `/api/visits/{id}/photos` y `/api/photos/{id}`.
- `/api/dashboard` y `/api/recommendations/*`, incluidos los contratos V2.

Todas las rutas personales requieren sesión. Las mutaciones requieren CSRF y
el `Origin` canónico. Preparar un lugar no persiste; el alta final ocurre sólo
mediante `POST /api/cafes`, que vuelve a consultar y validar Place Details.

## Seguridad, privacidad y datos Google

- Todas las consultas personales incluyen el propietario autenticado; un ID
  ajeno devuelve `404`.
- Cookies `HttpOnly`, `SameSite=Lax`, host-only y `Secure` fuera de desarrollo.
- `TrustedHostMiddleware`, CSP, protección de framing,
  `X-Content-Type-Options` y `Referrer-Policy` permanecen activos.
- Place IDs pueden persistirse; las coordenadas vencen a los 29 días.
- Nombre, dirección, barrio y coordenadas canónicos no se confían al navegador.
- La ubicación actual permanece en memoria y nunca se incorpora a URL, SQLite,
  logs ni storage del navegador.
- Fotos privadas requieren autenticación y propietario, y se validan y recodifican.
- Bases, backups, uploads, `.env`, claves y tokens nunca deben versionarse.

## Diseño y accesibilidad

El sistema visual “Cuaderno de recorrido cafetero contemporáneo” usa una paleta
crema, espresso, terracota y oliva, Georgia para títulos y fuentes del sistema
para interfaz. Mantiene HTML semántico, enlace para saltar al contenido, labels
visibles, regiones `aria-live`, foco perceptible, objetivos táctiles, diálogos
con retorno de foco, tablas equivalentes al gráfico y
`prefers-reduced-motion: reduce`.

El buscador de Places asociado al mapa es el recorrido accesible completo para
teclado. Los POI nativos son sólo complementarios. La grilla se verificó sin
overflow a 320, 768 y 1440 px; no se usa `overflow-x: hidden` para ocultar
defectos.

La estructura autenticada definitiva es **Descubrir**, **Mis cafeterías** —con
sus filtros incluidos—, **Mapa** y **Dashboard**. El gráfico omite etiquetas de
cero sobre los meses, usa ticks enteros únicos y reserva el desplazamiento
horizontal para pantallas estrechas. Las recomendaciones muestran cuatro
resultados por página mediante paginación local accesible.

## Skills UX locales

- **UI/UX Pro Max** se usa sólo con sus datos y scripts locales previamente
  inspeccionados, sin red ni dependencias nuevas.
- **21st UI Review** se usa únicamente como checklist textual. Están prohibidos
  su CLI, MCP, cuentas, API keys, servicios remotos, `21st review`, `--fix`,
  `npx`, React, shadcn y la creación de `.21st/`.

Las dos skills están fijadas a los SHA y licencias registrados en sus directorios
locales. Sus recomendaciones no reemplazan los contratos, tests ni decisiones
del proyecto.

## Limitaciones conocidas

- Auth0 puede revocar una sesión externa sin invalidar inmediatamente la sesión
  local; termina por logout o expiración local.
- Google Maps depende de cuota, facturación, disponibilidad y compatibilidad de
  sus componentes; el modo degradado conserva las funciones locales.
- La accesibilidad de los POI nativos depende de Google; por eso el buscador es
  el recorrido principal.
- SQLite y uploads son locales y no escalan horizontalmente.
- Las coordenadas Google deben refrescarse al vencer.
- Las interacciones de navegador POI, cancelación y retorno de foco son evidencia
  manual reproducible, no tests E2E persistentes; el proyecto no incorpora Node.
- La suite muestra `AuthlibDeprecationWarning` porque `authlib.jose` está
  deprecado. Debe migrarse a `joserfc` antes de actualizar a Authlib 2.0.

## Evidencia y estado de la base real

Los tests y la validación de navegador se realizaron offline con una base V4,
uploads, identidades, Places y mapa temporales o falsos. No se abrió `.env` ni
se usaron Auth0 o Google reales.

La base real fue migrada de V3 a V4 y verificada en un checkpoint independiente.
La auditoría final posterior se abrió sólo con SQLite read-only/query-only: el
archivo conservó `94208` bytes, integridad correcta, cero violaciones de claves
foráneas y conteos `10/8/4` para cafeterías, visitas y fotografías. Respecto de
la huella inmediatamente posterior a la migración existe una cafetería adicional
y cambió la huella del archivo; la evidencia no permite atribuir la causa, por
lo que se registra como **causa no demostrable**. Ver
[`docs/verification-v3.md`](docs/verification-v3.md).
