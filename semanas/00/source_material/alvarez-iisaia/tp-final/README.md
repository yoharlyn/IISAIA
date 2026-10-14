# Coffee Atlas V2

Coffee Atlas es un atlas y diario personal de cafeterías desarrollado como
proyecto educativo. FastAPI sirve la API y un frontend HTML, CSS y JavaScript
vanilla; SQLModel persiste datos locales en SQLite.

V2 incorpora Auth0, sesiones locales opacas, aislamiento por persona, direcciones
validadas en CABA, mapa y Places, visitas, fotos privadas, dashboard y
recomendaciones determinísticas. La especificación y el plan vigentes están en
[`docs/spec-v2.md`](docs/spec-v2.md) y [`docs/plan-v2.md`](docs/plan-v2.md). Los
documentos V1 permanecen congelados como registro histórico.

## Funcionalidades

- Login y registro mediante Auth0 Universal Login.
- Sesiones locales opacas: SQLite conserva sólo el hash del token.
- Cafeterías, visitas, fotos, dashboard y estadísticas aislados por usuario.
- Domicilio y cafeterías verificadas dentro de CABA mediante Place ID.
- Coordenadas de Places con vencimiento interno de 29 días.
- Mapa, geolocalización efímera y distancia Haversine.
- Historial de visitas con cuatro valoraciones opcionales.
- Hasta cinco fotos privadas por visita, validadas y recodificadas.
- Dashboard accesible con tablas equivalentes a cada visualización.
- Recomendaciones determinísticas con atribución y persistencia mínima.
- Modo degradado cuando Google Maps no está configurado o disponible.
- Páginas locales de Términos y Privacidad.

## Requisitos

- Python 3.11 o superior.
- [uv](https://docs.astral.sh/uv/).
- Una aplicación Auth0 de tipo **Regular Web Application**.
- Maps JavaScript API y Places API (New) habilitadas en Google Cloud.

No se utiliza Geocoding API, Node, bundler, framework frontend, Docker ni
Alembic.

## Configuración local

El único origen soportado es `http://127.0.0.1:8000`. No usar `localhost`:
representa otro host y mezclaría cookies, callbacks y orígenes autorizados.

1. Instalar dependencias con `uv sync`.
2. Copiar `.env.example` a `.env` y completar los valores localmente.
3. No pegar secretos en chats, logs, capturas o documentación.

Configuración Auth0:

```text
Callback:    http://127.0.0.1:8000/auth/callback
Logout:      http://127.0.0.1:8000/
Web origin:  http://127.0.0.1:8000
```

La clave web Google debe aceptar `http://127.0.0.1:8000/*`. Habilitar solamente
Maps JavaScript API y Places API (New), restringir cada clave por API y configurar
presupuesto y alertas. La clave web es visible al navegador; los secretos Auth0,
la clave de sesión y la clave servidor nunca se envían al frontend.

## Base de datos y migraciones

El startup nunca migra automáticamente una base existente. Si detecta V1 o una
V2 geográfica pendiente, se niega a iniciar y solicita el comando manual.

```bash
uv run python -m backend.migrations status --database data/coffee_atlas.db
uv run python -m backend.migrations backup \
  --database data/coffee_atlas.db \
  --output data/backups/coffee-atlas-AAAA-MM-DD-HHMMSS.db
uv run python -m backend.migrations upgrade \
  --database data/coffee_atlas.db \
  --backup data/backups/coffee-atlas-AAAA-MM-DD-HHMMSS.db
uv run python -m backend.migrations verify --database data/coffee_atlas.db
```

Restauración, siempre con servidor detenido y autorización independiente:

```bash
uv run python -m backend.migrations restore \
  --database data/coffee_atlas.db \
  --from data/backups/coffee-atlas-AAAA-MM-DD-HHMMSS.db
```

Ante un fallo no se repite ni se restaura automáticamente. SQLite y
`data/uploads/` deben respaldarse juntos.

## Ejecución

```bash
uv run fastapi dev backend/main.py \
  --factory \
  --host 127.0.0.1 \
  --port 8000 \
  --no-access-log
```

Abrir `http://127.0.0.1:8000`. La factory real carga `.env` y falla de forma
segura si faltan la clave de sesión o variables Auth0 requeridas.

## Sesiones y logout

- Inactividad máxima: 8 horas; duración absoluta: 7 días.
- No se almacenan access tokens ni refresh tokens Auth0.
- El logout elimina la sesión local, expira la cookie y luego intenta cerrar el
  SSO en Auth0.
- Si Auth0 está caído, la sesión local ya queda invalidada.
- Revocar o cerrar una sesión directamente en Auth0 no invalida inmediatamente
  una sesión local existente; termina por logout o expiración local.

## Privacidad y datos Google

- Place IDs pueden persistirse.
- La dirección seleccionada se guarda como dato de la transacción del usuario.
- Coordenadas de Places vencen a los 29 días.
- Componentes, rating, reseñas, estado comercial, apertura y enlace de Google
  Maps se usan en la respuesta actual y no forman un snapshot persistente.
- La ubicación actual permanece en memoria. Para recomendaciones viaja en el
  body de un `POST` sin caché; nunca en URLs, SQLite o storage del navegador.
- Fotos, notas, visitas y ratings personales son datos locales del usuario.

Más detalles: [Términos](http://127.0.0.1:8000/terms.html) y
[Privacidad](http://127.0.0.1:8000/privacy.html) con la aplicación local iniciada.

## Pruebas

```bash
UV_CACHE_DIR=/private/tmp/coffee-atlas-uv-cache uv run --offline pytest -q
UV_CACHE_DIR=/private/tmp/coffee-atlas-uv-cache uv run --offline python -m compileall backend
git diff --check
```

Los tests bloquean la red y usan SQLite y uploads temporales. El recorrido de
navegador está en [`docs/browser-checklist-v2.md`](docs/browser-checklist-v2.md)
y la evidencia en [`docs/verification-v2.md`](docs/verification-v2.md).

## Arquitectura

```text
Auth0 Universal Login
        | OIDC Authorization Code
        v
FastAPI -- sesión local opaca -- SQLite
   |                              |- users / sessions
   |                              |- cafes / visits / visit_photos
   |                              `- place_discoveries
   |- Places API (New)
   |- data/uploads/ privado
   `- frontend HTML/CSS/JS
          |- Maps JavaScript API
          `- navigator.geolocation
```

Los routers se registran antes del frontend estático. `frontend/js/api.js` es
la única capa HTTP del navegador y el contenido dinámico se construye con APIs
seguras del DOM.

## Estructura

El backend separa autenticación, configuración, migraciones, Places,
geografía, cafeterías, visitas, uploads, dashboard y recomendaciones. El
frontend mantiene módulos enfocados para sesión, API, mapa, Places, visitas,
dashboard y recomendaciones, sin proceso de build.

## Modelo de datos

El esquema contiene `users`, `sessions`, `cafes`, `visits`, `visit_photos`,
`place_discoveries` y metadata de migración. Cafeterías, visitas, fotos y
descubrimientos pertenecen a un usuario; el mismo Place ID puede existir para
propietarios distintos. El estado visitado y los ratings de cafetería se derivan
de las visitas.

## API

Rutas principales:

- `/auth/login`, `/auth/signup`, `/auth/callback` y `POST /auth/logout`.
- `/api/session`, `/api/config` y `/api/profile`.
- CRUD `/api/cafes` y `POST /api/cafes/search`.
- Visitas bajo `/api/cafes/{id}/visits` y `/api/visits/{id}`.
- Fotos bajo `/api/visits/{id}/photos` y `/api/photos/{id}`.
- `/api/dashboard` y `/api/recommendations/*`.

Todas las rutas personales requieren sesión y todas las mutaciones requieren
CSRF. Las búsquedas con ubicación actual usan `POST`, `Cache-Control: no-store`
y nunca query parameters de coordenadas.

## Seguridad

- Todas las consultas personales incluyen el propietario autenticado.
- IDs de otras personas devuelven `404`.
- Cookies `HttpOnly`, `SameSite=Lax`, host-only y `Secure` fuera de desarrollo.
- `TrustedHostMiddleware` acepta sólo el host canónico configurado.
- CSP compatible con Google Maps, protección de framing,
  `X-Content-Type-Options` y `Referrer-Policy`.
- Uploads con límites, validación de contenido, recodificación y acceso
  autenticado.
- Bodies sensibles, secretos y ubicación actual no se registran.

## Diseño y accesibilidad

La interfaz usa HTML semántico, labels visibles, regiones `aria-live`, foco
perceptible, diálogos con retorno de foco y tablas alternativas para los
gráficos. La grilla funciona sin overflow a 320, 768 y 1440 px; ningún estado
depende sólo del color.

## Proceso asistido por Codex

V2 se implementó por fases y checkpoints independientes. Auth0, migraciones y
Google tuvieron pruebas con dobles antes de cualquier verificación real. Cada
operación sobre la base real requirió autorización específica, backup y evidencia
sanitizada.

## Evidencia

La suite, la auditoría de seguridad y el navegador temporal están documentados
en [`docs/verification-v2.md`](docs/verification-v2.md). La comprobación final
usa proveedores falsos y datos temporales; los checkpoints reales anteriores no
se repiten sin autorización.

## Diferencias respecto del plan

- V1 anónima y global pasó a identidad Auth0 y datos personales aislados.
- La tabla única evolucionó a un modelo relacional; estado y ratings se derivan
  de visitas.
- El seed automático fue reemplazado por una migración manual con propietario.
- Direcciones libres pasaron a Place ID y validación geográfica de CABA.
- La ampliación geográfica requirió una migración adicional a esquema 3. Fue
  autorizada, respaldada y verificada en un checkpoint independiente; no se
  reescribe retroactivamente `docs/plan-v2.md`.
- La auditoría final detectó y corrigió encabezados de seguridad, validación
  fail-closed de la factory real y la documentación local de privacidad.
- El cierre no volvió a ejecutar `verify` sobre la base real porque quedó fuera
  de la autorización de Fase 5; se conserva el checkpoint de migración aceptado.

## Problemas encontrados

- La ruta del proyecto contiene Unicode y espacios; los comandos deben ejecutarse
  desde la raíz confirmada del repositorio.
- En entornos restringidos, usar una caché `uv` temporal y modo offline evita
  modificar la caché global o descargar dependencias.
- La suite informa una deprecación de `authlib.jose`; no se oculta.

## Límites deliberados

- Revocación Auth0 externa no inmediata y ausencia de refresh tokens.
- Dependencia de cuotas, facturación y disponibilidad de Google Maps.
- Las coordenadas Google deben refrescarse al vencer.
- SQLite y uploads son locales: no replican ni escalan horizontalmente.
- Migrar `authlib.jose` a `joserfc` antes de actualizar Authlib 2.
