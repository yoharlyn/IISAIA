# Coffee Atlas V2 — instrucciones del proyecto

## Propósito y límites

Coffee Atlas V2 usa FastAPI, SQLModel, SQLite y frontend HTML/CSS/JavaScript
vanilla. El contrato vigente está en `docs/spec-v2.md` y el orden histórico
aprobado en `docs/plan-v2.md`.

- Conservá `docs/spec.md`, `docs/plan.md`, `docs/spec-v2.md` y
  `docs/plan-v2.md` sin reescrituras retroactivas.
- No agregues frameworks frontend, Node, bundlers, Docker, Alembic, IA,
  funciones sociales ni almacenamiento cloud.
- Usá solamente Maps JavaScript API y Places API (New); no habilites Geocoding.
- La URL canónica es exclusivamente `http://127.0.0.1:8000`.
- Base, uploads, `.env`, claves y tokens son locales y nunca se versionan.

## Forma de trabajo

- Trabajá en cambios pequeños con tests y proveedores falsos por defecto.
- Los tests usan SQLite/uploads temporales y no realizan red.
- Migraciones o verificaciones sobre la base real requieren autorización
  independiente y servidor detenido; nunca se repiten o restauran solas.
- No abras ni imprimas `.env`; comprobá sólo presencia cuando corresponda.
- Antes de terminar, ejecutá tests afectados, suite, compilación y navegador.
- Los textos visibles, documentación y errores propios van en español.

## Contratos importantes

- Toda entidad personal queda aislada mediante el propietario autenticado.
- Auth0 usa Authorization Code y la aplicación guarda sólo sesiones hasheadas.
- Mutaciones requieren CSRF y `Origin`; un ID ajeno devuelve `404`.
- La ubicación actual es efímera: nunca URL, SQLite, logs ni storage.
- Place IDs pueden persistir; coordenadas vencen a los 29 días y el resto del
  contenido Google se mantiene vivo según `docs/spec-v2.md`.
- Fotos privadas se sirven sólo por endpoint autenticado.
- Registrá routers `/api` y `/auth` antes del frontend estático.
- `frontend/js/api.js` es la única capa HTTP del navegador.

## Lectura por contexto

- Backend y tests asociados: `backend/AGENTS.md`.
- Frontend, accesibilidad y navegador: `frontend/AGENTS.md`.
- Evidencia: `docs/verification-v2.md` y `docs/browser-checklist-v2.md`.
- Revisión final: `.codex/skills/preentrega-coffee-atlas/SKILL.md`.
