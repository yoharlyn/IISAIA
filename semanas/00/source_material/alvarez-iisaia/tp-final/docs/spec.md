# Coffee Atlas — especificación del MVP

## Producto

Coffee Atlas es un atlas y diario personal, local y sin autenticación para
registrar cafeterías visitadas o pendientes. Permite consultar, crear, editar y
eliminar cafeterías, administrar favoritos, calificarlas, buscarlas, filtrarlas
y ver estadísticas globales.

## Alcance funcional

- Listar cafeterías persistidas en SQLite mediante tarjetas.
- Mostrar nombre, barrio, descripción, imagen opcional, estado, favorito y
  ratings de café, comida, ambiente y atención.
- Crear, editar y eliminar con confirmación.
- Alternar favorito mediante la edición del recurso.
- Usar estados `PENDING` y `VISITED`.
- Buscar por nombre y filtrar por barrio, estado y favoritos.
- Mostrar total, visitadas, pendientes y favoritas.
- Mantener los datos después de reiniciar el servidor.

No incluye autenticación, mapas, servicios externos, recomendaciones, funciones
sociales, carga de archivos, cloud, frameworks frontend, build, Docker, Alembic
ni deploy.

## Arquitectura

Un único proceso FastAPI sirve los seis endpoints bajo `/api` y monta el
frontend estático en `/`. El frontend usa HTML, CSS y módulos ES nativos. La API
usa Pydantic, SQLModel y una sesión por request contra SQLite. La base local vive
en `data/coffee_atlas.db` y no se versiona.

El router de API se registra antes del montaje estático. `create_app()` permite
inyectar otra URL de base y desactivar o activar el seed para pruebas aisladas.

## Modelo `cafes`

| Campo | Regla |
|---|---|
| `id` | entero, PK autoincremental |
| `name` | texto obligatorio, trim, 1–100 |
| `neighborhood` | texto obligatorio, trim, 1–80 |
| `description` | texto obligatorio, trim, 1–600 |
| `image_url` | `null` o URL HTTP/HTTPS de hasta 2048 caracteres |
| `visit_status` | `PENDING` o `VISITED`; default `PENDING` |
| `is_favorite` | booleano; default `false` |
| cuatro ratings | `null` o entero 1–5 |
| `created_at` | UTC, generado por servidor, inmutable |
| `updated_at` | UTC, generado por servidor y renovado en `PATCH` |

No hay unicidad de nombre. Las valoraciones son opcionales e independientes del
estado. Los schemas prohíben campos extra; un `PATCH` debe incluir al menos un
campo y sólo imagen y ratings aceptan `null`.

## Contrato HTTP

| Método | Path | Resultado |
|---|---|---|
| `GET` | `/api/cafes` | `200` lista ordenada por actualización e ID descendentes |
| `POST` | `/api/cafes` | `201` cafetería creada |
| `GET` | `/api/cafes/{cafe_id}` | `200` cafetería o `404` |
| `PATCH` | `/api/cafes/{cafe_id}` | `200` cafetería actualizada, `404` o `422` |
| `DELETE` | `/api/cafes/{cafe_id}` | `204` sin body o `404` |
| `GET` | `/api/stats` | `200` contadores globales |

`GET /api/cafes` acepta `q`, `neighborhood`, `visit_status` e `is_favorite`.
Los filtros se combinan con `AND`; búsqueda y barrio no distinguen mayúsculas.
`%` y `_` en `q` son caracteres literales. Una colección sin coincidencias es
`200 []`. Un recurso ausente responde
`{"detail":"Cafetería no encontrada."}`. La validación inválida usa `422`.

Las estadísticas exponen exactamente `total`, `visited`, `pending` y
`favorites`, siempre sobre toda la tabla.

## Seed

Al arrancar se crean tablas y, sólo si `cafes` está vacía, se insertan en una
transacción siete cafeterías ficticias: Bruma Café, Oliva Tostadores, Patio
Terracota, Andén Café, Nido Espresso, Umbral Café y Surco Café. Cuatro están
visitadas, tres pendientes y tres son favoritas. Reiniciar no duplica filas ni
repone las eliminadas.

## Experiencia y accesibilidad

La interfaz usa una paleta crema, espresso, oliva y terracota, grilla responsive
desde 320 px y tarjetas con imagen o fallback. Tiene estados distintos de carga,
colección vacía, cero resultados, error y éxito. Los envíos deshabilitan su botón.

El HTML es semántico, los labels son visibles y asociados, el foco tiene
contraste, los mensajes dinámicos usan regiones vivas y los diálogos admiten
Escape y restauran el foco. Toda la operación puede realizarse con teclado. No
se usan emojis como sustituto de iconos o etiquetas.

## Criterio de finalización

Los tests de contrato y persistencia pasan; el frontend consume la API real; las
mutaciones sobreviven un reinicio; el checklist de navegador se completa en 320,
768 y 1440 px; el README describe decisiones, proceso, verificación, problemas y
límites reales de la entrega.

