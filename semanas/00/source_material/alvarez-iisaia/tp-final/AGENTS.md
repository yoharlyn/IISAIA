# Coffee Atlas — instrucciones del proyecto

## Propósito y límites

Coffee Atlas es un atlas personal de cafeterías. El frontend usa HTML, CSS y
JavaScript vanilla; FastAPI expone exactamente seis endpoints bajo `/api` y
persiste una única tabla `cafes` con SQLModel y SQLite.

- No agregues autenticación, mapas, APIs externas, IA, funciones sociales,
  carga de archivos, Docker, Alembic, frameworks frontend ni procesos de build.
- No agregues endpoints fuera del contrato de `docs/spec.md`.
- Conservá `docs/plan.md` como el plan aprobado: cualquier diferencia entre el
  plan y el resultado se explica en el README, no se oculta reescribiendo el plan.
- Todo el trabajo debe permanecer dentro de este directorio `tp-final`.
- La base `data/coffee_atlas.db` es un artefacto local: nunca se versiona.

## Forma de trabajo

- Trabajá en cambios pequeños y verificables, con tests antes o junto al
  comportamiento correspondiente.
- Usá `uv` para dependencias y comandos Python.
- Antes de declarar una tarea terminada, ejecutá la verificación proporcional:
  tests afectados, suite completa cuando corresponda y navegador para la UI.
- No hagas commits con tests fallando ni incluyas cambios externos a este
  directorio.
- Los textos visibles, el README y los mensajes de error propios van en español.
- Preferí funciones y módulos enfocados; evitá abstracciones sin uso real.

## Contratos importantes

- Registrar todos los routers `/api` antes de montar los archivos estáticos en
  `/`.
- Los tests usan SQLite temporal y no deben tocar la base de desarrollo.
- El backend no descarga imágenes: sólo valida y guarda URLs HTTP/HTTPS.
- El frontend interpreta HTTP únicamente en `frontend/js/api.js` y construye
  contenido dinámico mediante APIs seguras del DOM.
- Los cuatro contadores de `/api/stats` son globales, no dependen de filtros.

## Lectura por contexto

- Para reglas de datos y API, leé `backend/AGENTS.md`.
- Para interfaz, accesibilidad y estados, leé `frontend/AGENTS.md`.
- Para una revisión final, usá la skill
  `.codex/skills/preentrega-coffee-atlas/SKILL.md`.

