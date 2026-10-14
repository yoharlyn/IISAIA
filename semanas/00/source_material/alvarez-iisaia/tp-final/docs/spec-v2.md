# Coffee Atlas V2 — especificación funcional y técnica

## 1. Propósito

Coffee Atlas V2 es un atlas personal de cafeterías para usuarios autenticados. Mantiene una única aplicación FastAPI con SQLModel, SQLite y un frontend HTML, CSS y JavaScript vanilla. La versión incorpora autenticación con Auth0, aislamiento por usuario, ubicaciones verificadas en CABA, mapa, visitas, fotografías privadas, dashboard y recomendaciones determinísticas.

Esta especificación define el contrato V2. `docs/spec.md` y `docs/plan.md` documentan V1 y permanecen congelados.

## 2. Decisiones y límites

- Auth0 mediante Authorization Code Flow y Universal Login.
- Sesiones locales opacas; SQLite conserva solamente el hash del token.
- Todos los datos personales quedan aislados por propietario.
- Origen canónico único: `http://127.0.0.1:8000`.
- Integraciones Google permitidas: Maps JavaScript API y Places API (New).
- Geocoding API no se habilita: Place Details (New) cubre los campos requeridos.
- Las siete cafeterías V1 se migran al propietario indicado por `LEGACY_OWNER_AUTH0_SUB` y quedan con ubicación pendiente.
- El estado visitado y las puntuaciones se derivan de visitas; no se persisten en `cafes`.
- La ubicación actual del navegador es efímera y nunca se incorpora a URLs, SQLite, cachés persistentes ni logs ordinarios.
- Las llamadas reales a Auth0 y Google sólo se realizan después de sus checkpoints manuales.

Quedan fuera de alcance autenticación propia, contraseñas locales, funciones sociales, contenido público, frameworks frontend, TypeScript, bundlers, Docker, Alembic, despliegue cloud, Google Routes/Route Matrix, Places Photos, almacenamiento cloud, IA y fechas manuales de apertura.

## 3. Arquitectura

```text
Auth0 Universal Login
        │ OIDC Authorization Code
        ▼
FastAPI ── sesión local opaca ── SQLite
   │                              ├─ users
   │                              ├─ sessions
   │                              ├─ cafes
   │                              ├─ visits
   │                              ├─ visit_photos
   │                              └─ place_discoveries
   │
   ├─ Places API (New): Details + Nearby Search
   ├─ data/uploads/: fotografías privadas
   └─ frontend vanilla
          ├─ Maps JavaScript API
          ├─ PlaceAutocompleteElement
          └─ navigator.geolocation
```

Las rutas `/api` y `/auth` se registran antes del montaje de archivos estáticos. Los tests usan SQLite y directorios temporales, bloquean la red y nunca tocan la base de desarrollo.

## 4. Persistencia de datos Google

Las condiciones vigentes de Google se revisarán antes de implementar la integración. No se asume que todo el contenido de Places pueda almacenarse indefinidamente.

| Dato | Origen y política |
|---|---|
| Place ID | Dato Google persistible indefinidamente. Se registra `place_id_checked_at`; después de 12 meses se refresca solicitando sólo `id`. |
| Dirección seleccionada | Se persiste como dato de la transacción iniciada y confirmada por el usuario mediante Autocomplete. |
| `formattedAddress` de Details | Se usa para cotejo durante el request; no se crea un snapshot adicional. |
| Componentes de dirección | Sólo memoria del request. Se descartan tras validar CABA. |
| Coordenadas de Places | SQLite con `location_fetched_at` y vencimiento interno a 29 días. Vencidas, deben refrescarse o dejar de usarse. |
| Rating Google | Sólo respuesta viva/memoria de la vista; sin SQLite ni storage del navegador. |
| Cantidad de reseñas | Igual que rating; debe volver a consultarse. |
| Estado comercial | Sólo request; debe volver a consultarse. |
| Fecha de apertura | Sólo request; visible únicamente si la respuesta actual informa una apertura futura verificable. |
| Enlace de Google Maps | Sólo request; no se persiste. |
| Nombre Google | Sólo request. Al guardar una recomendación, el usuario confirma o edita un nombre local. |
| Evidencia de CABA | Dato propio: resultado, fecha, versión del polígono y barrio calculado localmente. |
| Primera/última detección | Dato propio asociado al Place ID y propietario. |
| Ratings, notas, favoritos y fotos personales | Datos locales del usuario, sin TTL de Google. |
| Ubicación actual | Memoria efímera con consentimiento explícito; nunca se persiste. |

No habrá una tabla de snapshots generales de Google. `place_discoveries` sólo contendrá propietario, Place ID y fechas propias.

### Validación de dirección

1. El usuario selecciona una dirección mediante `PlaceAutocompleteElement`.
2. El frontend envía Place ID, dirección seleccionada y tipo de operación.
3. El backend solicita a Place Details `id`, `formattedAddress`, `addressComponents` y `location`.
4. Compara selección y respuesta.
5. Valida componentes en memoria y pertenencia al polígono oficial de CABA.
6. Persiste Place ID, dirección confirmada, coordenadas con TTL y evidencia local.
7. Descarta componentes y dirección de Details al terminar el request.

Una recomendación no puede copiar silenciosamente la dirección de Nearby Search: para guardarla, el usuario debe confirmarla con Autocomplete.

### Atribución, términos y privacidad

- Todo contenido Google mostrado fuera del mapa tendrá atribución visible “Google Maps”.
- Los datos de Google y los datos personales se presentarán separados.
- Rating y reseñas se identificarán como procedentes de Google Maps.
- No se ocultará ninguna atribución provista por mapa o autocompletado.
- Habrá páginas de términos y privacidad.
- La privacidad explicará los datos enviados a Auth0 y Google, el envío transitorio de ubicación actual, el almacenamiento local de domicilio, visitas y fotos, y la no persistencia de la ubicación actual.

## 5. Modelo de datos

### `users`

- `id` y `auth0_sub` único.
- `identity_status`: `PENDING_LOGIN` o `ACTIVE`.
- Email observado desde Auth0 y nombre visible editable localmente.
- Domicilio opcional: Place ID, dirección seleccionada, coordenadas con vencimiento, barrio y evidencia CABA.
- Timestamps.

### `sessions`

- Hash del token opaco y `user_id`.
- Hash del token CSRF.
- `created_at`, `last_seen_at`, `idle_expires_at`, `absolute_expires_at`.
- Nunca access tokens ni refresh tokens de Auth0.

### `cafes`

- `owner_id`, nombre y descripción locales, favorito e imagen externa heredada opcional.
- Place ID, dirección seleccionada, coordenadas con TTL, barrio y evidencia CABA.
- `location_status`: `VERIFIED`, `NEEDS_LOCATION` o `EXPIRED`.
- Índice único parcial `(owner_id, place_id)` cuando exista Place ID.
- Timestamps.

El mismo Place ID puede pertenecer a usuarios distintos.

### `visits`

- `owner_id`, `cafe_id`, fecha, nota y `date_is_estimated`.
- Cuatro ratings opcionales entre 1 y 5.
- Timestamps.

`VISITED` se deriva de una o más visitas; `PENDING`, de su ausencia.

### `visit_photos`

- `owner_id`, `visit_id`, nombre interno, MIME, tamaño, dimensiones y hash.
- Texto alternativo/caption y timestamp.

### `place_discoveries`

- `owner_id`, Place ID, primera y última detección.
- Sin nombre, rating, dirección ni otros detalles Google.

SQLite usa `PRAGMA foreign_keys=ON`. Las relaciones sensibles repiten o validan `owner_id` para impedir asociaciones cruzadas.

## 6. Autenticación, sesión y seguridad

Authlib implementará Authorization Code Flow con Universal Login. Coffee Atlas no almacena contraseñas. Registro, recuperación y defensas de credenciales se delegan a Auth0.

En el callback se validan `state`, `nonce`, emisor, audiencia y expiración; se crea o reconcilia el usuario, se rota la sesión y se emite un token aleatorio cuya versión en claro sólo reside en una cookie:

- `HttpOnly`;
- `SameSite=Lax`;
- host-only para `127.0.0.1`;
- `Path=/`;
- `Secure`, salvo la excepción HTTP local documentada.

La sesión vence tras 8 horas de inactividad o 7 días absolutos. El límite absoluto no se renueva. No se usan refresh tokens, por lo que después del vencimiento se requiere autenticar nuevamente.

Una revocación o cierre externo en Auth0 no invalida inmediatamente una sesión local ya emitida. Sin back-channel logout, introspección periódica o refresh tokens, la aplicación no recibe ese evento. La sesión local termina por logout local, expiración, eliminación de su fila o invalidación local global del usuario.

`POST /auth/logout` elimina la sesión local, expira la cookie con `Max-Age=0` y redirige a la URL fija de logout Auth0. Si Auth0 está caído, la sesión local queda invalidada, aunque el SSO externo podría continuar activo.

Controles obligatorios:

- consultas siempre filtradas por `owner_id=current_user.id`;
- recursos ajenos responden `404`;
- CSRF con token y validación de `Origin`;
- destinos de redirección configurados, no arbitrarios;
- contenido dinámico con APIs seguras del DOM;
- hosts externos constantes para evitar SSRF;
- sin tokens, cuerpos sensibles, domicilios ni coordenadas actuales en logs;
- CSP, `X-Content-Type-Options`, `Referrer-Policy` y protección de framing;
- rate limiting local para recomendaciones;
- uploads con validación real y límites.

## 7. Origen canónico y configuración

El único origen soportado es `http://127.0.0.1:8000`; `localhost` no se admite para evitar mezclar cookies, sesiones y callbacks.

```dotenv
APP_BASE_URL=http://127.0.0.1:8000
APP_ENV=development
SESSION_SECRET=

AUTH0_DOMAIN=
AUTH0_CLIENT_ID=
AUTH0_CLIENT_SECRET=
AUTH0_CALLBACK_URL=http://127.0.0.1:8000/auth/callback
AUTH0_LOGOUT_RETURN_URL=http://127.0.0.1:8000/
LEGACY_OWNER_AUTH0_SUB=

GOOGLE_MAPS_BROWSER_KEY=
GOOGLE_MAPS_SERVER_KEY=
GOOGLE_MAP_ID=

DATABASE_URL=
UPLOAD_DIR=
```

Auth0 callback, logout y web origin, cookies, validación de `Origin`, CSP, `TrustedHostMiddleware`, documentación y comandos usarán el mismo host. La clave web Google se restringirá al referrer `http://127.0.0.1:8000/*` y a las APIs necesarias.

Los valores reales sólo estarán en `.env`, ignorado por Git. Ningún secreto se enviará al navegador, al chat, a logs, capturas o documentación.

## 8. Ubicación actual, distancia y búsqueda

`navigator.geolocation` mantiene las coordenadas sólo en memoria. El mapa y el cálculo local de Haversine no las envían al servidor. No se usan query strings, historial, SQLite, `localStorage`, `sessionStorage` ni IndexedDB.

Cuando Nearby Search requiera la ubicación actual, se usa exclusivamente un POST explícito:

```http
POST /api/recommendations/search
Content-Type: application/json
Cache-Control: no-store
X-CSRF-Token: ...

{
  "origin": {
    "type": "current",
    "latitude": -34.60,
    "longitude": -58.38
  },
  "radius_km": 3
}
```

El body no se registra ni se copia a archivos, métricas, traces, cachés o errores. La respuesta usa `Cache-Control: no-store`; hay consentimiento explícito y rate limit por usuario. Para domicilio se envía `origin.type="home"` sin exponer coordenadas en la URL.

Haversine usa radio terrestre `6371.0088 km`, el valor completo para ordenar/filtrar y una cifra decimal en UI. El radio del atlas es 0,5–20 km y el de recomendaciones, como máximo 5 km. La interfaz aclara: “Distancia en línea recta, no tiempo de viaje”.

## 9. Migración V1

La migración nunca se ejecuta automáticamente. Al iniciar, una base inexistente recibe esquema V2; una V2 arranca; una V1 se rechaza con instrucciones y no se modifica.

Comandos reproducibles:

```bash
uv run python -m backend.migrations status --database data/coffee_atlas.db
uv run python -m backend.migrations backup --database data/coffee_atlas.db --output data/backups/coffee_atlas-v1-AAAA-MM-DD-HHMMSS.db
uv run python -m backend.migrations upgrade --database data/coffee_atlas.db --backup data/backups/coffee_atlas-v1-AAAA-MM-DD-HHMMSS.db
uv run python -m backend.migrations verify --database data/coffee_atlas.db
uv run python -m backend.migrations restore --database data/coffee_atlas.db --from data/backups/coffee_atlas-v1-AAAA-MM-DD-HHMMSS.db
```

Garantías:

- backup previo obligatorio e integridad SQLite comprobada;
- transacción y rollback total ante fallo;
- backup original inmutable;
- `schema_migrations` confirmado sólo al finalizar;
- segunda ejecución idempotente, sin escritura;
- restauración con validación de rutas, backup de rescate y reemplazo atómico;
- siete cafeterías `NEEDS_LOCATION`;
- cuatro cafeterías visitadas generan cuatro visitas de fecha estimada;
- ratings y favoritos V1 se conservan;
- verificación mediante metadata de migración, sin asumir que el propietario carecía de datos previos.

`LEGACY_OWNER_AUTH0_SUB` es obligatorio. La migración busca ese `auth0_sub`, reutiliza tanto un usuario `PENDING_LOGIN` como uno `ACTIVE`, y sólo crea un placeholder si no existe. Nunca reconcilia por email. El primer callback del placeholder lo activa. No se crean duplicados; toda inconsistencia provoca rollback.

La base real sólo se inspecciona y migra en los checkpoints expresos definidos en `docs/plan-v2.md`.

## 10. Visitas y fotografías

Las visitas admiten CRUD, fecha, nota y cuatro ratings opcionales de 1 a 5. Promedios y estado de cafetería se derivan. Al eliminar la última visita, la cafetería vuelve a pendiente.

Fotografías:

- máximo 5 por visita y 5 MiB por archivo;
- máximo 20 MiB acumulados por visita;
- JPEG, PNG o WebP;
- Pillow decodifica y recodifica;
- máximo 20 megapíxeles; animaciones rechazadas;
- UUID y extensión decididos por el servidor;
- ruta `data/uploads/{owner_id}/{visit_id}/`;
- acceso exclusivo por endpoint autenticado;
- eliminación mediante cuarentena temporal y transacción;
- fallback ante archivo faltante.

SQLite y `data/uploads/` deben respaldarse juntos. El almacenamiento local no replica ni escala.

## 11. Dashboard, recomendaciones y novedades

El dashboard personal incluye total, visitadas, pendientes, favoritas, visitas por mes, evolución acumulada de 12 meses, promedio de ratings, distribución por barrio, mejor puntuadas y pendientes cercanas. CSS y SVG nativo tendrán alternativa tabular accesible.

Nearby Search se ejecuta sólo por acción del usuario y devuelve hasta 20 candidatos. La máscara mínima incluye ID, nombre, dirección, ubicación, componentes, tipo, estado comercial, rating, cantidad de reseñas, fecha de apertura y enlace de Google Maps.

```text
score =
  0,35 × cercanía
+ 0,30 × rating_google
+ 0,15 × confianza_reseñas
+ 0,10 × novedad_en_atlas
+ 0,10 × afinidad_personal
```

- `cercanía = max(0, 1 - distancia/radio)`.
- `rating_google = rating/5`.
- `confianza_reseñas = log(1 + min(reseñas,1000)) / log(1001)`.
- Novedad: 1 no guardada; 0,65 pendiente; 0,20 visitada.
- Afinidad: promedio bayesiano por barrio, activo desde 5 visitas puntuadas y 2 barrios.
- Pesos sin datos se redistribuyen proporcionalmente.
- Empates: distancia, reseñas y nombre.

La UI explica los factores. Rating y reseñas Google nunca se persisten.

Denominaciones honestas:

- “Próxima apertura”: `openingDate` futura y estado verificable en la respuesta actual.
- “Descubierta recientemente”: `first_seen_at` propio y Place ID.
- “Agregada recientemente”: `Cafe.created_at`.
- No se usa “recién inaugurada” sin fuente verificable.

## 12. API V2

### Autenticación y perfil

| Método | Ruta | Uso |
|---|---|---|
| `GET` | `/auth/login` | Iniciar Authorization Code Flow |
| `GET` | `/auth/signup` | Universal Login en modo registro |
| `GET` | `/auth/callback` | Validar OIDC y crear sesión local |
| `POST` | `/auth/logout` | Invalidar sesión local y cerrar Auth0 |
| `GET` | `/api/session` | Estado, perfil mínimo y CSRF |
| `GET` | `/api/config` | Clave web restringida, Map ID y flags |
| `GET/PATCH` | `/api/profile` | Perfil y domicilio |

### Cafeterías y estadísticas

- `GET/POST /api/cafes`
- `GET/PATCH/DELETE /api/cafes/{id}`
- `GET /api/stats`
- `POST /api/cafes/search`

Los seis endpoints V1 se conservan semánticamente, ahora autenticados y limitados al usuario.

### Visitas, fotos y dashboard

- `GET/POST /api/cafes/{id}/visits`
- `PATCH/DELETE /api/visits/{id}`
- `POST /api/visits/{id}/photos`
- `GET/DELETE /api/photos/{id}`
- `GET /api/dashboard`

### Recomendaciones

- `POST /api/recommendations/search`
- `POST /api/recommendations/{place_id}/prepare-save`
- `POST /api/recommendations/{place_id}/save`

`prepare-save` entrega datos vivos; `save` exige nombre local y dirección confirmada mediante Autocomplete.

## 13. Interfaz, accesibilidad y degradación

Pantallas: login/registro, atlas, mapa, detalle, visitas/fotos, dashboard, recomendaciones/novedades, perfil/domicilio, términos y privacidad.

Se contemplan estados de sesión, Auth0 caído, Google no configurado/sin cuota, domicilio faltante, ubicación heredada pendiente, geolocalización concedida/rechazada/no disponible/timeout, coordenadas vencidas, upload inválido/archivo faltante y carga/error/vacío/cero resultados.

Requisitos de accesibilidad:

- 320, 768 y 1440 px sin desborde;
- teclado completo y retorno de foco en diálogos;
- `aria-live` para estados;
- autocompletado operable por teclado;
- tablas equivalentes para gráficos;
- tarjeta y marcador sincronizados con texto/`aria-current`;
- ninguna información depende sólo del color.

Sin Google siguen disponibles sesión, CRUD no geográfico, filtros, favoritos, estadísticas, visitas, fotos, dashboard y dirección elegida. Coordenadas vigentes pueden usarse localmente; al vencer se deshabilitan mapa, distancia y radio hasta refrescar. No se crean nuevas ubicaciones ni recomendaciones.

## 14. Dependencias y archivos

Dependencias nuevas previstas: `authlib`, `itsdangerous`, `httpx` directa, `python-multipart`, `Pillow` y `python-dotenv`. No se agrega librería de gráficos ni dependencia JavaScript.

Se crearán `docs/plan-v2.md`, `docs/verification-v2.md`, `docs/browser-checklist-v2.md` y `.env.example`. Después del CHECKPOINT 0 y sólo con nueva aprobación podrán actualizarse README, instrucciones, skill de preentrega, `.gitignore`, `pyproject.toml` y `uv.lock`. `docs/spec.md` y `docs/plan.md` no se modifican.

## 15. Separación entre acciones locales y externas

El agente puede implementar y probar con mocks, ejecutar validaciones locales sin red, documentar configuración y verificar integraciones después de que el usuario configure credenciales. Sólo puede migrar la base real con autorización específica.

El agente no puede crear cuentas externas, aceptar contratos, configurar facturación, registrar medios de pago, solicitar secretos por chat, imprimir secretos, incluir valores reales en capturas/documentación, versionar `.env` ni efectuar llamadas reales antes del checkpoint correspondiente.

## 16. Criterios generales de aceptación

- Aislamiento demostrado con al menos dos usuarios.
- Suite sin red con Auth0 y Places falsos.
- Migración/backup/verify/restore probados sobre copias temporales antes de tocar la base real.
- Base real migrada sólo después de inspección y autorización independientes.
- Integraciones reales verificadas sólo después de configuración manual.
- Interfaz comprobada a 320, 768 y 1440 px, teclado y consola limpia.
- Documentación V1 intacta y ausencia de secretos en Git.
- Cada fase se detiene en su checkpoint y requiere una aprobación explícita nueva.
