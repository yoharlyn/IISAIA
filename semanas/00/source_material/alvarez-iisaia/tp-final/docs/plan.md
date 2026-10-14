# Plan aprobado — Coffee Atlas

Este documento queda congelado como evidencia del plan aprobado. Las diferencias
que surjan durante la implementación se registrarán en el README y en
`docs/verification.md`, sin reescribir retroactivamente este plan.

## Autorizaciones

La ejecución tiene dos bloques. El primero sólo crea esta documentación,
`AGENTS.md`, las instrucciones específicas, la skill de preentrega, `.gitignore`
y `data/.gitkeep`. Después se informa el árbol y el estado de Git y se espera una
segunda aprobación. Antes de esa segunda aprobación no se crea branch, no se
instalan dependencias, no se escribe código, no se inicia la app y no se hacen
commits.

La implementación completa comienza únicamente con la segunda aprobación.

## Decisiones cerradas

- Frontend HTML5, CSS3 y JavaScript vanilla con módulos ES, sin build.
- Backend Python 3.11+, FastAPI, Pydantic y SQLModel.
- Una tabla SQLite `cafes` y un archivo local ignorado por Git.
- Exactamente seis endpoints: listado, creación, detalle, edición, eliminación y
  estadísticas.
- Seed idempotente de siete cafeterías que sólo corre sobre una tabla vacía.
- Una sola aplicación FastAPI sirve `/api` y el frontend.
- Sin autenticación, mapas, APIs externas, IA, social, uploads, Docker, Alembic
  ni despliegue.
- Estadísticas globales; filtros combinados con `AND`; sin paginación.
- Ratings opcionales e independientes del estado.
- No se planifican subagentes.

## Estructura final

```text
tp-final/
├── .codex/skills/preentrega-coffee-atlas/SKILL.md
├── data/.gitkeep
├── docs/{browser-checklist.md,plan.md,spec.md,verification.md}
├── backend/{AGENTS.md,__init__.py,db.py,main.py,models.py,routes.py,schemas.py,seed.py}
├── frontend/
│   ├── AGENTS.md
│   ├── index.html
│   ├── css/styles.css
│   └── js/{api.js,app.js,ui.js}
├── tests/{conftest.py,test_cafes_read.py,test_cafes_write.py,test_seed.py,test_static.py}
├── .gitignore
├── AGENTS.md
├── README.md
├── pyproject.toml
└── uv.lock
```

`data/coffee_atlas.db` se genera en ejecución y no se versiona.

## Tareas, verificaciones y tiempos

### 1. Diseño e instrucciones — 45 minutos

Validar ruta y repositorio; guardar spec, plan, instrucciones, skill, ignore y
`.gitkeep`. Verificar árbol, `git status --short`, `git diff --stat` y
`git diff --check`. Detenerse en el checkpoint sin branch, commits, dependencias
ni código.

### 2. Entorno y aplicación mínima — 50 minutos

Tras la segunda aprobación, crear `codex/coffee-atlas-mvp`, declarar dependencias
con `uv` y crear app factory, sesión por request, montaje estático y el primer
test de integración. Verificar con `uv run pytest tests/test_static.py -q`.

### 3. Modelo, schemas y seed — 1 hora 10 minutos

Escribir primero pruebas de primer arranque, segundo arranque y no reinserción.
Implementar tabla, enum, restricciones, timestamps, schemas y seed transaccional.
Verificar con `uv run pytest tests/test_seed.py -q`.

### 4. Lecturas, filtros y estadísticas — 1 hora 15 minutos

Probar listado, detalle, orden, búsqueda literal, filtros combinados, colección
vacía, errores y contadores. Implementar los tres endpoints de lectura. Verificar
con `uv run pytest tests/test_cafes_read.py -q`.

### 5. Creación, edición y eliminación — 1 hora 30 minutos

Probar creación, normalización, rangos, campos extra, patch parcial y vacío,
favorito, fechas, delete, errores y persistencia. Implementar `POST`, `PATCH` y
`DELETE`. Verificar con `uv run pytest tests/test_cafes_write.py -q`.

### 6. Shell visual y cliente HTTP — 1 hora 10 minutos

Probar que HTML, CSS y módulos se entregan y que el HTML contiene semántica,
labels, regiones vivas y diálogos. Implementar layout y `api.js`. Verificar con
`uv run pytest tests/test_static.py -q`.

### 7. Tarjetas, filtros y estadísticas — 1 hora 10 minutos

Implementar carga, tarjetas DOM seguras, imágenes y fallback, ratings, barrios,
filtros, contadores y estados. Verificar siete tarjetas y combinaciones contra
las respuestas crudas de la API.

### 8. Mutaciones en la interfaz — 1 hora 20 minutos

Implementar crear, editar, favoritos, ratings, confirmación de eliminación,
bloqueo durante requests y mensajes. Verificar CRUD completo desde navegador y
persistencia tras reinicio.

### 9. Navegador y accesibilidad — 1 hora 25 minutos

Crear checklist y evidencia. Verificar 320, 768 y 1440 px, teclado, foco,
diálogos, estados, imagen rota, API caída, reinicio y consola. Usar Playwright si
está disponible; en caso contrario dejar un procedimiento manual reproducible.

### 10. README y cierre — 1 hora 15 minutos

Ejecutar la skill de preentrega, suite, compilación y checks de Git. Redactar el
README como informe con instalación, arquitectura, contrato, decisiones, proceso
asistido, evidencia, diferencias, problemas y límites.

Tiempo total estimado: **11 horas 50 minutos**, sin contar esperas de aprobación.

## Git después de la segunda aprobación

Rama: `codex/coffee-atlas-mvp`.

Commits previstos:

1. `docs: fijar especificación y plan de coffee atlas`
2. `chore: preparar aplicación y entorno con uv`
3. `feat: agregar modelo persistente y seed idempotente`
4. `feat: exponer consultas filtros y estadísticas`
5. `feat: completar altas ediciones y bajas`
6. `feat: construir interfaz del atlas`
7. `feat: integrar formularios favoritos y eliminación`
8. `test: verificar experiencia completa en navegador`
9. `docs: cerrar informe y evidencia de entrega`

## Pruebas y aceptación

- API: validación, CRUD, códigos 200/201/204/404/422, orden, búsqueda, filtros,
  UTC y estadísticas.
- Integración: SQLite temporal real, clientes sucesivos, seed, reinicio y
  montaje conjunto de API y frontend.
- Frontend: entrega estática y recorrido dinámico en navegador sin sumar Node.
- Navegador: carga, filtros, todas las mutaciones, fallback, API caída, teclado,
  responsive, persistencia y consola limpia.

Comandos finales previstos:

```bash
uv sync
uv run pytest -q
uv run python -m compileall backend
uv run fastapi dev backend/main.py
git diff --check
git status --short
```

## Riesgos y recortes

Ante retrasos se eliminan, en orden, transiciones, adornos, imágenes externas del
seed y documentación redundante. No se recortan los seis endpoints, CRUD,
persistencia, favoritos, estados, ratings, búsqueda, filtros, estadísticas,
tests esenciales, navegador, accesibilidad básica ni README. No se amplía el
alcance para consumir el margen de tiempo.
