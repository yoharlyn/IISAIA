# Coffee Atlas

Trabajo Práctico Final de Introducción a la Ingeniería de Software Asistida por
IA. Coffee Atlas es un atlas y diario personal para guardar cafeterías visitadas
o pendientes, calificarlas, marcarlas como favoritas y volver a encontrarlas con
búsqueda y filtros.

El flujo es real de punta a punta: el navegador consume una API FastAPI, la API
lee y escribe una base SQLite y los cambios permanecen después de reiniciar el
servidor.

## Funcionalidades

- Tarjetas con nombre, barrio, descripción, foto o fallback, estado y ratings.
- Alta, edición y eliminación con confirmación.
- Favoritos desde cada tarjeta.
- Estados `PENDING` y `VISITED`.
- Ratings opcionales de 1 a 5 para café, comida, ambiente y atención.
- Búsqueda parcial por nombre.
- Filtros combinables por barrio, estado y favoritos.
- Estadísticas globales de total, visitadas, pendientes y favoritas.
- Seed idempotente con siete cafeterías ficticias.
- Estados visibles de carga, vacío, cero resultados, error y éxito.
- Interfaz responsive y operable por teclado.

## Requisitos y ejecución

- Python 3.11 o superior.
- [uv](https://docs.astral.sh/uv/).

Desde este directorio:

```bash
uv sync
uv run fastapi dev backend/main.py
```

Abrir `http://127.0.0.1:8000`. La documentación interactiva de la API está en
`http://127.0.0.1:8000/docs`.

Si el puerto 8000 está ocupado:

```bash
uv run fastapi dev backend/main.py --port 8765
```

La primera ejecución crea `data/coffee_atlas.db` y carga siete registros. La
base está ignorada por Git. No hay variables de entorno ni servicios externos
obligatorios.

## Pruebas

```bash
uv run pytest -q
uv run python -m compileall backend
```

Los tests usan una SQLite temporal, no modifican `data/coffee_atlas.db` y no
necesitan red. La evidencia completa está en
[`docs/verification.md`](docs/verification.md) y el recorrido manual reproducible
en [`docs/browser-checklist.md`](docs/browser-checklist.md).

## Arquitectura

```text
Navegador: HTML + CSS + módulos ES
                 │ fetch, mismo origen
                 ▼
FastAPI: /api + frontend estático en /
                 │ SQLModel Session por request
                 ▼
SQLite: data/coffee_atlas.db
```

Un solo proceso sirve API y frontend. `backend/main.py` registra el router `/api`
antes de montar `StaticFiles` en `/`; así no hacen falta CORS, Node ni un segundo
servidor.

El backend está separado en:

- `db.py`: engine y sesión por request.
- `models.py`: tabla `Cafe`, enum y restricciones de base.
- `schemas.py`: entradas y salidas Pydantic.
- `seed.py`: siete datos iniciales y condición idempotente.
- `routes.py`: los seis endpoints.
- `main.py`: app factory, lifespan y archivos estáticos.

El frontend usa tres módulos:

- `api.js`: única capa que conoce `fetch` y traduce errores.
- `ui.js`: crea tarjetas y estados con APIs seguras del DOM.
- `app.js`: coordina filtros, diálogos, mutaciones y recargas.

## Estructura

```text
tp-final/
├── .codex/skills/preentrega-coffee-atlas/SKILL.md
├── data/.gitkeep
├── docs/
│   ├── browser-checklist.md
│   ├── plan.md
│   ├── spec.md
│   └── verification.md
├── backend/
│   ├── AGENTS.md
│   ├── __init__.py
│   ├── db.py
│   ├── main.py
│   ├── models.py
│   ├── routes.py
│   ├── schemas.py
│   └── seed.py
├── frontend/
│   ├── AGENTS.md
│   ├── index.html
│   ├── css/styles.css
│   └── js/{api.js,app.js,ui.js}
├── tests/
│   ├── conftest.py
│   ├── test_cafes_read.py
│   ├── test_cafes_write.py
│   ├── test_seed.py
│   └── test_static.py
├── .gitignore
├── AGENTS.md
├── pyproject.toml
└── uv.lock
```

## Modelo de datos

La única tabla es `cafes`:

| Campo | Regla |
|---|---|
| `id` | PK autoincremental |
| `name` | obligatorio, 1–100 |
| `neighborhood` | obligatorio, 1–80 |
| `description` | obligatorio, 1–600 |
| `image_url` | URL HTTP/HTTPS opcional |
| `visit_status` | `PENDING` o `VISITED` |
| `is_favorite` | booleano |
| cuatro ratings | `null` o entero de 1 a 5 |
| `created_at` | UTC, creado por servidor |
| `updated_at` | UTC, renovado en cada edición |

Los campos se validan con Pydantic y las invariantes principales también tienen
restricciones SQLite. Los nombres no son únicos para permitir sucursales. Las
valoraciones son opcionales e independientes del estado.

## API

| Método | Path | Éxito | Errores de contrato |
|---|---|---|---|
| `GET` | `/api/cafes` | `200` | `422` query inválida |
| `POST` | `/api/cafes` | `201` | `422` body inválido |
| `GET` | `/api/cafes/{id}` | `200` | `404`, `422` |
| `PATCH` | `/api/cafes/{id}` | `200` | `404`, `422` |
| `DELETE` | `/api/cafes/{id}` | `204` | `404`, `422` |
| `GET` | `/api/stats` | `200` | — |

El listado acepta `q`, `neighborhood`, `visit_status` e `is_favorite`. Los
filtros se combinan con `AND`, búsqueda y barrio no distinguen mayúsculas y los
caracteres `%` y `_` se buscan literalmente. El orden es por `updated_at` e `id`
descendentes. Las estadísticas siempre representan toda la colección.

Ejemplo:

```http
PATCH /api/cafes/1
Content-Type: application/json

{"is_favorite":true,"coffee_rating":5}
```

## Decisiones técnicas

### Una sola tabla

No hay usuarios, visitas históricas ni entidades relacionadas. Separar barrios,
ratings o favoritos en otras tablas agregaría joins y migraciones sin resolver
un requisito del MVP. La tabla única aplica YAGNI y sigue siendo fácil de
explicar.

### Schemas separados del modelo

`CafeCreate`, `CafeUpdate` y `CafeRead` evitan que el cliente escriba IDs o
fechas. `CafeUpdate` distingue un campo ausente de un `null` deliberado y rechaza
un body vacío.

### Seed sólo sobre tabla vacía

El seed se inserta en una transacción únicamente cuando no existe ninguna fila.
Esto permite reiniciar sin duplicar y, sobre todo, evita que una cafetería
eliminada reaparezca.

### Frontend sin build

Los módulos ES se sirven tal como están. Se descartaron React y bundlers porque
el estado de esta aplicación cabe en un módulo coordinador y el TP pide un stack
explicable con una sola orden de ejecución.

### Imágenes como referencia externa

El servidor valida y almacena la URL, pero nunca descarga archivos. El navegador
reserva el espacio, usa carga diferida y muestra un fallback si la URL falta o
falla.

## Diseño y accesibilidad

La identidad usa crema, espresso, oliva y terracota. La grilla tiene una columna
a 320 px, dos a 768 px y tres a 1440 px. Los estados y acciones no dependen sólo
del color.

- HTML semántico y jerarquía de encabezados.
- Labels visibles, `fieldset` para ratings y regiones `aria-live`.
- Foco de alto contraste.
- Diálogos nativos que cierran con Escape y restauran el foco.
- Botones con acciones textuales, sin emojis como etiquetas.
- Botones deshabilitados durante mutaciones.
- Creación dinámica con `textContent`, sin insertar datos remotos como HTML.

## Proceso asistido por Codex

El trabajo comenzó en Plan Mode. Primero se inspeccionó el ejemplo del curso en
modo de sólo lectura y se diseñaron producto, contrato, estructura, pruebas,
commits y recortes. La primera autorización creó únicamente `docs/spec.md`,
`docs/plan.md`, instrucciones y la skill; hubo un checkpoint antes del código.

La segunda autorización habilitó una branch y la implementación incremental. Los
tests se escribieron antes o junto a cada comportamiento. Cada capa se verificó
antes de pasar a la siguiente y el cierre usó HTTP real y navegador con
Playwright.

El proyecto versiona instrucciones nativas para Codex:

- `AGENTS.md` global.
- `backend/AGENTS.md` y `frontend/AGENTS.md` para contexto local.
- `preentrega-coffee-atlas`, una skill diagnóstica que no repara sin permiso.

No se usaron subagentes: el dominio es pequeño y mantener API, UI y evidencia en
un mismo contexto evitó coordinación innecesaria.

## Evidencia

La suite final tiene 25 tests. En el navegador se verificaron los tres anchos,
búsqueda y filtros, alta, edición, favorito, fallback, cancelación de eliminación,
Escape, foco, consola y persistencia tras reiniciar. El registro temporal fue
eliminado y la base quedó con las siete cafeterías del seed.

## Diferencias respecto del plan

- Las tareas de shell visual y mutaciones terminaron en un único commit funcional
  porque `index.html`, `app.js` y `ui.js` forman un contrato inseparable. Se
  conservaron todos los comportamientos y verificaciones planeados.
- La eliminación definitiva desde el botón no se ejecutó automáticamente durante
  la sesión de navegador: se abrió y canceló el diálogo, mientras que el `DELETE`
  real se comprobó con tests y HTTP. El paso manual está documentado.
- No hicieron falta recortes de alcance, transiciones complejas ni archivos de
  imágenes locales.

## Problemas encontrados

### Unicode en la ruta

macOS representó los acentos con Unicode NFD, mientras la ruta escrita en el
enunciado estaba en NFC. Antes de escribir se confirmó `samefile=True` y la
igualdad después de normalizar a NFC; así se evitó crear un directorio paralelo.

### Permisos del repositorio y caché

El entorno permitía escribir el proyecto, pero no `.git` ni la caché de `uv` sin
autorización puntual. Se solicitaron permisos sólo para branch/commits y para los
comandos `uv`, sin ampliar el alcance de archivos.

### Validación de la skill

Antes de instalar dependencias, el validador de skills no pudo importar PyYAML.
No se instaló nada durante el checkpoint. Después, `uv` incorporó PyYAML como
dependencia transitiva de FastAPI y permitió completar la verificación final.

## Límites deliberados

No hay autenticación, mapas, geolocalización, APIs de cafeterías, recomendaciones,
funciones sociales, uploads, cloud, Docker, Alembic ni deploy. Tampoco hay
paginación: Coffee Atlas es un diario personal y el MVP privilegia un contrato
pequeño, persistente y totalmente demostrable.

