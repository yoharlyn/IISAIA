# DentalHub — Versión 1

Aplicación web vertical para que un odontólogo autenticado consulte un catálogo de productos odontológicos almacenado en SQLite. Incluye FastAPI, SQLAlchemy 2, Alembic, HTML/CSS/JavaScript vanilla y una prueba E2E real con Playwright.

## Alcance

Esta versión implementa exclusivamente:

- login y logout de un usuario activo con rol `DENTIST`;
- sesión firmada en cookie `HttpOnly`;
- consulta de la identidad autenticada;
- catálogo protegido con búsqueda, categoría, tipo implante y paginación;
- cuatro tablas: `users`, `categories`, `products` e `implant_specs`;
- cuatro endpoints REST bajo `/api/v1`.

No incluye administración, perfil, carrito, órdenes, pagos, comprobantes, notificaciones, fabricantes, distribuidores ni envíos.

## Requisitos

- Python 3.11–3.14.
- [`uv`](https://docs.astral.sh/uv/).
- Chromium administrado por Playwright, solo para E2E.

No requiere Node.js, Docker ni compilación del frontend.

## Instalación

```bash
uv python install 3.11
uv sync --frozen
uv run playwright install chromium
cp .env.example .env
```

Generá un secreto de sesión local de al menos 32 caracteres y reemplazá `SESSION_SECRET` en `.env`. El archivo `.env`, la base y los artefactos están excluidos de Git.

## Base, seed y ejecución

```bash
uv run alembic upgrade head
SEED_DENTIST_PASSWORD='DemoLocal123!' uv run python -m backend.scripts.seed
uv run uvicorn backend.main:app --reload
```

Abrí <http://127.0.0.1:8000/login>.

Credencial únicamente para demostración local:

- usuario: `dentista.demo`
- contraseña: `DemoLocal123!`, solo si fue la usada al ejecutar el seed.

El seed exige `SEED_DENTIST_PASSWORD`, acepta `SEED_DENTIST_USERNAME` y es idempotente: actualiza las claves naturales sin duplicar filas. No uses la credencial de demostración fuera de un entorno local.

## Variables

| Variable | Propósito | Valor local habitual |
|---|---|---|
| `APP_ENV` | `development`, `test` o `production` | `development` |
| `DATABASE_URL` | URL SQLAlchemy de SQLite | `sqlite:///./var/app.db` |
| `SESSION_SECRET` | Firma de sesión, mínimo 32 caracteres en producción | secreto aleatorio |
| `SESSION_MAX_AGE_SECONDS` | Vida máxima de la sesión | `28800` |
| `SESSION_COOKIE_SECURE` | Envía cookie solo por HTTPS | `false` local, obligatorio en producción |
| `ALLOWED_ORIGINS` | Lista CORS separada por comas | orígenes locales explícitos |
| `TRUSTED_ORIGINS` | Orígenes aceptados por CSRF | orígenes locales explícitos |
| `LOG_LEVEL` | Nivel de log | `INFO` |
| `SEED_DENTIST_USERNAME` | Usuario de demostración | `dentista.demo` |
| `SEED_DENTIST_PASSWORD` | Clave recibida por el seed | obligatoria al sembrar |

## API V1

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `GET /api/v1/products`

El contrato completo está en [`openapi.yaml`](openapi.yaml). La aplicación no expone Swagger, ReDoc ni un endpoint de esquema. Para detectar deriva:

```bash
uv run python -m backend.scripts.check_openapi --check
```

## Seguridad

- Las contraseñas usan Argon2id con sal aleatoria.
- La cookie de sesión está firmada, expira, es `HttpOnly`, `SameSite=Lax` y se marca `Secure` en producción.
- Cada petición autenticada vuelve a comprobar que el usuario exista, esté activo y tenga rol `DENTIST`.
- Los `POST` exigen JSON, `X-CSRF-Protection: 1` y un `Origin`/`Referer` confiable.
- CORS nunca usa `*` con credenciales.
- Cinco fallos de login por usuario e IP dentro de quince minutos activan un bloqueo local temporal. Para múltiples procesos será necesario un almacén compartido.
- Los logs contienen método, ruta, status, duración y request ID, pero no cuerpos, cookies ni contraseñas.

La sesión de V1 es stateless. Logout elimina la cookie del cliente; una copia robada seguiría siendo válida hasta expirar. Una revocación central requeriría persistencia adicional y queda fuera de las cuatro tablas autorizadas.

## Calidad y pruebas

```bash
uv sync --frozen
uv run ruff check .
uv run ruff format --check .
uv run pytest --cov=backend --cov-report=term-missing
uv run python -m backend.scripts.check_openapi --check
uv run pytest tests/e2e -q
uv run alembic check
```

Las pruebas cubren migraciones upgrade/downgrade, restricciones y FKs, seed repetible, hashes, login, expiración, cookies por entorno, CSRF, CORS, rate limit, autorización, catálogo, filtros, contrato y estructura del frontend. El E2E crea una base temporal, migra, siembra, inicia Uvicorn y conduce Chromium por login → catálogo → búsqueda → logout → rechazo sin sesión.

Los `401` de `/auth/me` que produce deliberadamente la guarda al abrir login sin sesión o luego del logout son excluidos de la lista de errores inesperados del E2E; cualquier otro error de consola o JavaScript hace fallar la prueba.

## Arquitectura

La aplicación utiliza una arquitectura por capas sencilla. FastAPI sirve tanto la API REST como los archivos del frontend, por lo que navegador y backend comparten el mismo origen. Esto simplifica el uso seguro de cookies y evita depender de un servidor web o proceso de compilación adicional.

El flujo principal de una petición es:

```text
Navegador
  │  HTML, CSS y módulos JavaScript
  │  fetch JSON + cookie de sesión
  ▼
Routers FastAPI (`backend/api`)
  │  validación, sesión y autorización
  ▼
Servicios (`backend/services`)
  │  autenticación y reglas de consulta
  ▼
Modelos SQLAlchemy (`backend/models`)
  │
  ▼
SQLite
```

Los routers se organizan por recurso en lugar de concentrarse en un único `routes.py`. Cada archivo crea un `APIRouter` y `backend/main.py` lo incorpora mediante `app.include_router(...)`.

```text
tp-final/
├── backend/
│   ├── main.py                 # Crea FastAPI, registra routers y sirve el frontend
│   ├── config.py               # Lee y valida la configuración de entorno
│   ├── db.py                   # Engine, sesiones SQLAlchemy y claves foráneas SQLite
│   ├── errors.py               # Formato uniforme de errores JSON
│   ├── logging.py              # Request ID y log de acceso sin datos sensibles
│   ├── api/
│   │   ├── auth.py             # Login, logout y usuario autenticado
│   │   ├── products.py         # Listado, búsqueda, filtros y paginación
│   │   └── dependencies.py     # Sesión, rol DENTIST y protección CSRF
│   ├── services/
│   │   ├── auth.py             # Argon2, validación y firma de sesiones
│   │   ├── catalog.py          # Consulta parametrizada del catálogo
│   │   └── rate_limit.py       # Límite básico de intentos de login
│   ├── models/
│   │   ├── base.py             # Base declarativa y timestamps
│   │   ├── user.py             # Usuario y valores válidos de rol
│   │   └── catalog.py          # Categorías, productos e implantes
│   ├── schemas/                # Entradas y respuestas Pydantic de la API
│   ├── migrations/             # Configuración y versiones de Alembic
│   └── scripts/
│       ├── seed.py             # Datos iniciales idempotentes
│       └── check_openapi.py    # Verifica OpenAPI contra la implementación
├── frontend/
│   ├── login.html              # Formulario de autenticación
│   ├── catalog.html            # Vista protegida del odontólogo
│   └── assets/
│       ├── css/app.css         # Diseño responsive y tokens visuales
│       ├── fonts/              # DM Sans y licencia local
│       └── js/                 # Cliente API, sesión, catálogo y utilidades
├── tests/
│   ├── e2e/                    # Flujo completo con Playwright y Chromium
│   └── test_*.py               # Pruebas unitarias y de integración
├── openapi.yaml                # Contrato REST OpenAPI 3.1 versionado
├── alembic.ini                 # Configuración principal de migraciones
├── pyproject.toml              # Dependencias y herramientas de calidad
└── uv.lock                     # Versiones exactas y reproducibles
```

### Responsabilidades de las capas

- **Frontend:** presenta las vistas, gestiona estados de carga, error y vacío, y consume la API. No contiene productos simulados ni decide permisos de seguridad.
- **API:** transforma HTTP en llamadas a servicios, valida entradas con Pydantic y aplica las dependencias de autenticación y autorización.
- **Servicios:** concentra la lógica de autenticación, sesiones, limitación de intentos y construcción del catálogo paginado.
- **Persistencia:** los modelos SQLAlchemy representan las cuatro tablas de V1; Alembic controla cómo crear o revertir el esquema.
- **Contrato:** `openapi.yaml` documenta exclusivamente los cuatro endpoints implementados y se compara automáticamente con el esquema generado por FastAPI.
- **Pruebas:** las pruebas de integración usan SQLite real y el E2E inicia Uvicorn, migra una base temporal y conduce un navegador real.

## Decisiones evolutivas

`manufacturer_name` es descriptivo en V1. Una versión posterior agregará `manufacturer_id` nullable, mapeará y respaldará los nombres existentes, hará el backfill, validará la correspondencia y recreará la tabla con FK no nula antes de retirar la columna textual.

La búsqueda con comodines es suficiente para el catálogo mínimo; no se incorpora FTS. Las categorías disponibles viajan en la respuesta paginada para no añadir un quinto endpoint.

## Roadmap no implementado

1. Perfil, administración de usuarios y propiedad del catálogo.
2. Carrito monofabricante, stock transaccional y órdenes.
3. Comprobantes, rechazo/reintento, aprobación, historial y notificaciones.
4. Liberación del fabricante, tracking y despacho.
5. Almacenamiento externo, rate limit compartido, métricas y despliegue.
