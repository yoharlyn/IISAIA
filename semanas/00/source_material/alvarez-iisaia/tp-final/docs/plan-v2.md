# Coffee Atlas V2 — plan de ejecución aprobado

## 1. Reglas de ejecución

Este plan implementa `docs/spec-v2.md` en tareas pequeñas y verificables. Cada checkpoint es una barrera obligatoria: el agente debe mostrar evidencia, detenerse y esperar una aprobación explícita nueva. La aprobación de una fase no autoriza automáticamente la siguiente.

Reglas permanentes:

- origen canónico único: `http://127.0.0.1:8000`;
- tests antes o junto al comportamiento;
- `uv` para dependencias y comandos Python;
- tests sin red por defecto;
- secretos exclusivamente en `.env` local ignorado;
- ningún commit con tests fallando;
- `docs/spec.md` y `docs/plan.md` permanecen congelados;
- la migración V1 nunca se ejecuta automáticamente;
- no se realizan acciones externas en nombre del usuario.

## 2. Fase 0 — documentación aprobada

### Tarea 0.1 — especificación y plan V2

- Objetivo: guardar exclusivamente el contrato aprobado.
- Archivos: `docs/spec-v2.md`, `docs/plan-v2.md`.
- Tests: ninguno.
- Validación:

  ```bash
  git diff -- docs/spec-v2.md docs/plan-v2.md
  git diff --check
  git status --short
  ```

- Criterio de aceptación: sólo esos dos archivos aparecen como nuevos o modificados; los documentos V1 están intactos; no hay código, dependencias, configuración ni commits.
- Commit previsto: ninguno antes del checkpoint. Después de una nueva aprobación: `docs: definir especificación y plan de coffee atlas v2`.
- Dependencias: autorización inicial explícita.
- Credenciales externas: no.

## CHECKPOINT 0 — documentación

1. Mostrar el diff completo de ambos documentos.
2. Mostrar `git status --short`.
3. Confirmar que no cambió ningún otro archivo.
4. Detenerse.
5. Esperar aprobación antes de commit, código, dependencias, configuración o instrucciones.

## 3. Fase 1 — autenticación, sesiones, propiedad y migración

### Tarea 1.1 — configuración y dependencias

- Objetivo: configuración tipada, URL canónica y dependencias.
- Archivos: `pyproject.toml`, `uv.lock`, `backend/config.py`, `.env.example`, `.gitignore`, `tests/test_config.py`.
- Tests: variables faltantes, URL no canónica y secretos no expuestos.
- Validación: `uv run pytest tests/test_config.py -q` y `git diff --check`.
- Aceptación: configuración segura y `.env` ignorado.
- Commit: `chore: preparar configuración segura de v2`.
- Dependencias: CHECKPOINT 0 aprobado.
- Credenciales: no.

### Tarea 1.2 — modelos de usuario y sesión

- Objetivo: tablas `users` y `sessions`, cookies opacas y CSRF.
- Archivos: modelos, seguridad, base de datos, app factory y `tests/test_sessions.py`.
- Tests: hash, expiración inactiva/absoluta, rotación, CSRF e invalidación.
- Validación: `uv run pytest tests/test_sessions.py -q`.
- Aceptación: ningún token en claro y cookies inválidas rechazadas.
- Commit: `feat: agregar sesiones locales opacas`.
- Dependencias: T1.1.
- Credenciales: no.

### Tarea 1.3 — adaptador Auth0 y rutas

- Objetivo: OIDC detrás de un adaptador inyectable.
- Archivos: `backend/auth.py`, `backend/auth_routes.py`, `backend/main.py`, `tests/test_auth.py`.
- Tests: `state`, `nonce`, callback, signup, errores, logout y Auth0 caído.
- Validación: `uv run pytest tests/test_auth.py tests/test_sessions.py -q`.
- Aceptación: flujo completo con proveedor falso y cero red.
- Commit: `feat: integrar auth0 mediante un adaptador verificable`.
- Dependencias: T1.2.
- Credenciales: no.

### Tarea 1.4 — propiedad y aislamiento

- Objetivo: agregar `owner_id` y proteger los seis endpoints V1.
- Archivos: modelos, schemas, rutas, fixtures y tests existentes adaptados.
- Tests: dos usuarios, IDs cruzados, estadísticas personales y respuestas `401/404`.
- Validación: `uv run pytest tests/test_cafes_read.py tests/test_cafes_write.py tests/test_authorization.py -q`.
- Aceptación: ninguna operación cruza propietarios.
- Commit: `feat: aislar el atlas por usuario`.
- Dependencias: T1.2.
- Credenciales: no.

### Tarea 1.5 — migrador, backup y restauración

- Objetivo: comandos explícitos y migración transaccional.
- Archivos: `backend/migrations.py`, `tests/test_migrations.py`.
- Tests: `status`, `backup`, `upgrade`, `verify`, `restore`, rollback parcial, idempotencia, integridad, placeholder creado/activado al primer login, usuario `ACTIVE` preexistente con el mismo `auth0_sub` y ausencia de duplicados.
- Resolución del propietario:
  1. buscar por `auth0_sub`;
  2. reutilizar usuario `PENDING_LOGIN` o `ACTIVE`;
  3. si no existe, crear placeholder;
  4. nunca reconciliar por email;
  5. ante inconsistencias, rollback total.
- Validación: `uv run pytest tests/test_migrations.py -q`.
- Aceptación: se usan sólo bases temporales; la base real queda intacta.
- Commit: `feat: agregar migración respaldada desde v1`.
- Dependencias: T1.4.
- Credenciales: no.

### Tarea 1.6 — frontend de sesión

- Objetivo: login, signup, expiración, logout y perfil mínimo.
- Archivos: HTML, CSS, `frontend/js/api.js`, `frontend/js/app.js`, `frontend/js/auth.js` y tests estáticos.
- Tests: shell, enlaces, `401` y ausencia de secretos.
- Validación: `uv run pytest tests/test_static.py tests/test_auth.py -q`.
- Aceptación: UI funcional con proveedor falso.
- Commit: `feat: incorporar experiencia de sesión`.
- Dependencias: T1.3.
- Credenciales: no.

## CHECKPOINT 1A — autenticación y migración simuladas

1. Ejecutar todos los tests de fase sin red.
2. Mostrar resultados, diff y estado de Git.
3. Confirmar que `data/coffee_atlas.db` no cambió.
4. Detenerse y esperar aprobación para la configuración manual de Auth0.

### Configuración manual Auth0

El usuario, no el agente:

1. crea el tenant;
2. crea una Regular Web Application;
3. configura callback `http://127.0.0.1:8000/auth/callback`;
4. configura logout y web origin `http://127.0.0.1:8000`;
5. habilita registro;
6. crea la cuenta propietaria desde el panel;
7. todavía no inicia sesión en Coffee Atlas;
8. obtiene su `sub`/`user_id`;
9. configura `LEGACY_OWNER_AUTH0_SUB` en `.env` sin compartirlo por chat;
10. completa las restantes variables locales sin exponer secretos.

El agente se limita a proporcionar instrucciones, comprobar la presencia de variables sin imprimir valores y esperar confirmación.

## CHECKPOINT 1B — inspección de la base real

Con el servidor detenido, el agente ejecuta únicamente:

```bash
uv run python -m backend.migrations status \
  --database data/coffee_atlas.db
```

Luego muestra el resultado sanitizado, la ruta absoluta de la base, la confirmación de servidor detenido, la ruta absoluta propuesta para el backup, los comandos siguientes y la confirmación de que no escribió nada. Se detiene y solicita una autorización independiente antes de backup o migración.

### Tarea 1.7 — backup y migración real

Sólo tras esa autorización específica:

1. ejecutar nuevamente los tests del migrador;
2. crear el backup con nombre fechado;
3. comprobar su integridad SQLite;
4. ejecutar `upgrade`;
5. ejecutar `verify`;
6. mostrar resultados sanitizados.

- Archivos afectados: base y backup locales ignorados por Git.
- Aceptación: backup íntegro y verificación completa.
- Commit: ninguno.
- Dependencias: CHECKPOINT 1B autorizado.
- Credenciales: sólo se comprueba la presencia de `LEGACY_OWNER_AUTH0_SUB`; nunca se muestra el valor.

Ante cualquier fallo, el agente se detiene inmediatamente: no repite, no restaura y no vuelve a modificar la base sin una nueva autorización explícita.

## CHECKPOINT 1C — migración real verificada

1. Mostrar resultados de backup, `upgrade` y `verify`.
2. Mostrar estado de Git.
3. Confirmar que todavía no hubo login real.
4. Detenerse y esperar aprobación para el primer login.

### Tarea 1.8 — primera verificación Auth0 real

- Objetivo: verificar registro/login/callback/sesión/logout y reconciliación real.
- Tests previos: `uv run pytest tests/test_auth.py tests/test_sessions.py tests/test_migrations.py -q`.
- Ejecución: `uv run fastapi dev backend/main.py --host 127.0.0.1 --port 8000`.
- Pasos: iniciar sesión con la cuenta propietaria, reconciliar por `auth0_sub`, confirmar una sola fila, verificar acceso a siete registros, comprobar sesión/CSRF, cerrar sesión y verificar invalidación local.
- Aceptación: reconciliación sin duplicados y secretos ausentes de evidencia/logs.
- Commit previsto: `test: verificar autenticación y reconciliación reales`.
- Dependencias: CHECKPOINT 1C aprobado.

## CHECKPOINT 1D — cierre de fase

Mostrar tests, evidencia sanitizada, diff, commits y estado. Detenerse y esperar aprobación para Fase 2.

## 4. Fase 2 — Google, CABA, mapa, cercanía y recomendaciones

### Tarea 2.1 — adaptador Places

- Objetivo: Place Details y Nearby Search inyectables.
- Archivos: `backend/google_places.py`, configuración y tests.
- Tests: field masks, timeout, cuota, respuestas incompletas y bloqueo de red.
- Validación: `uv run pytest tests/test_google_places.py -q`.
- Aceptación: proveedor falso completo, cero red.
- Commit: `feat: agregar adaptador para places api new`.
- Dependencias: Fase 1 aprobada.
- Credenciales: no.

### Tarea 2.2 — CABA y TTL

- Objetivo: polígono oficial, Place ID y coordenadas con TTL de 29 días.
- Archivos: `backend/geo.py`, GeoJSON con procedencia/licencia, modelos, schemas y tests.
- Tests: interior, borde, exterior, componentes, expiración y purga.
- Validación: `uv run pytest tests/test_locations.py -q`.
- Aceptación: componentes crudos no persisten y coordenadas vencidas no se usan.
- Commit: `feat: validar ubicaciones dentro de caba`.
- Dependencias: T2.1.
- Credenciales: no.

### Tarea 2.3 — perfil y cafeterías geográficas

- Objetivo: domicilio y dirección verificada.
- Archivos: rutas de perfil/cafés, modelos, schemas y frontend de perfil.
- Tests: selección obligatoria, texto libre rechazado, duplicados por propietario y usuarios distintos.
- Validación: `uv run pytest tests/test_profile.py tests/test_locations.py tests/test_cafes_write.py -q`.
- Aceptación: ubicación sólo tras Details falso y validación CABA.
- Commit: `feat: agregar domicilios y ubicaciones verificadas`.
- Dependencias: T2.2.
- Credenciales: no.

### Tarea 2.4 — mapa y geolocalización

- Objetivo: mapa, marcadores y estados del permiso.
- Archivos: `frontend/js/map.js`, app/UI, HTML y CSS.
- Tests: estáticos y dobles de navegador.
- Validación: `uv run pytest tests/test_static.py tests/test_profile.py -q`.
- Aceptación: ubicación actual ausente de URL, storage y API para mapa local.
- Commit: `feat: incorporar mapa y geolocalización efímera`.
- Dependencias: T2.3.
- Credenciales: no.

### Tarea 2.5 — Haversine y búsqueda POST

- Objetivo: cercanía y radio sin query params sensibles.
- Archivos: `backend/distance.py`, rutas, frontend y tests.
- Tests: distancias, radio, redondeo, `no-store` y ausencia de persistencia.
- Validación: `uv run pytest tests/test_distance.py tests/test_cafes_read.py -q`.
- Aceptación: coordenadas actuales ausentes de URL, base, caché y logs.
- Commit: `feat: ordenar cafeterías por cercanía`.
- Dependencias: T2.2.
- Credenciales: no.

### Tarea 2.6 — recomendaciones con dobles

- Objetivo: Nearby, fórmula, novedades y guardado confirmado.
- Archivos: servicio y rutas de recomendaciones, modelos/schemas y tests.
- Tests: score, datos faltantes, descubrimientos, apertura, duplicados y política de persistencia.
- Validación: `uv run pytest tests/test_recommendations.py tests/test_google_places.py -q`.
- Aceptación: la base contiene sólo Place ID y fechas propias para descubrimientos; rating y reseñas no persisten.
- Commit: `feat: agregar recomendaciones determinísticas`.
- Dependencias: T2.1, T2.2 y T2.5.
- Credenciales: no.

### Tarea 2.7 — autocompletado y UI falsa

- Objetivo: widget, teclado, errores, atribución y degradación.
- Archivos: `frontend/js/places.js`, `frontend/js/recommendations.js`, HTML, CSS y UI.
- Tests: estáticos y bootstrap falso.
- Validación: `uv run pytest tests/test_static.py tests/test_recommendations.py -q`.
- Aceptación: sin APIs legacy y modo degradado funcional.
- Commit: `feat: completar experiencia geográfica sin red`.
- Dependencias: T2.3, T2.4 y T2.6.
- Credenciales: no.

## CHECKPOINT 2A — Google automático

Ejecutar todos los tests de fase sin red, mostrar resultados, diff y estado, confirmar que no hubo consumo de cuota y detenerse.

### Configuración manual Google Cloud

El usuario, no el agente:

1. crea o selecciona el proyecto;
2. asocia facturación;
3. habilita únicamente Maps JavaScript API y Places API (New);
4. crea la clave web;
5. crea la clave de servidor;
6. crea el Map ID;
7. restringe la clave web por referrer y APIs;
8. restringe la clave servidor por API y, cuando sea viable, por IP;
9. configura cuotas, presupuesto y alertas;
10. completa `.env` sin compartir secretos.

El agente no crea cuentas, configura facturación, registra medios de pago ni acepta condiciones. Espera confirmación explícita.

### Tarea 2.8 — verificación Google real

- Objetivo: probar mapa, Autocomplete, Details, Nearby y atribución.
- Validación automática: `uv run pytest tests/test_google_places.py tests/test_locations.py tests/test_recommendations.py -q`.
- Ejecución: `uv run fastapi dev backend/main.py --host 127.0.0.1 --port 8000`.
- Aceptación: dirección CABA aceptada, exterior rechazado, atribución visible y consumo esperado.
- Commit: `test: verificar integración real con google maps`.
- Dependencias: confirmación manual Google.

## CHECKPOINT 2B — cierre geográfico

Mostrar evidencia sanitizada, consumo esperado, diff, commits y estado. Detenerse y esperar aprobación para Fase 3.

## 5. Fase 3 — visitas y fotos

### Tarea 3.1 — visitas y ratings derivados

- Objetivo: CRUD de visitas y estado/promedios derivados.
- Archivos: modelos, schemas, rutas, agregados y tests.
- Tests: CRUD, propiedad, transición de estado y promedios.
- Validación: `uv run pytest tests/test_visits.py tests/test_authorization.py -q`.
- Aceptación: ningún rating persiste en `cafes`.
- Commit: `feat: registrar historial de visitas`.
- Dependencias: Fase 2 aprobada.
- Credenciales: no.

### Tarea 3.2 — almacenamiento privado

- Objetivo: uploads validados y aislados.
- Archivos: servicio/rutas/modelos de uploads, `.gitignore` y tests.
- Tests: MIME, tamaño, píxeles, traversal, propiedad, faltantes y rollback.
- Validación: `uv run pytest tests/test_photos.py -q`.
- Aceptación: rutas generadas por servidor y sólo directorios temporales en tests.
- Commit: `feat: agregar fotografías privadas de visitas`.
- Dependencias: T3.1.
- Credenciales: no.

### Tarea 3.3 — UI de visitas y fotos

- Objetivo: experiencia accesible de historial y carga.
- Archivos: `frontend/js/visits.js`, `frontend/js/api.js`, HTML, CSS y tests.
- Tests: estáticos, visitas y fotos.
- Validación: `uv run pytest tests/test_static.py tests/test_visits.py tests/test_photos.py -q`.
- Aceptación: teclado, foco, progreso, límites y fallback.
- Commit: `feat: completar experiencia de visitas`.
- Dependencias: T3.1 y T3.2.
- Credenciales: no.

## CHECKPOINT 3 — visitas y fotos

Mostrar suite, diff, commits y estado. Detenerse y esperar aprobación para Fase 4.

## 6. Fase 4 — dashboard y presentación de recomendaciones

### Tarea 4.1 — agregados

- Objetivo: métricas personales del dashboard.
- Archivos: backend de dashboard, rutas, schemas y tests.
- Tests: usuarios separados, meses vacíos, promedios y cercanía.
- Validación: `uv run pytest tests/test_dashboard.py -q`.
- Aceptación: datos exclusivamente del usuario autenticado.
- Commit: `feat: agregar dashboard personal`.
- Dependencias: T3.1.
- Credenciales: no.

### Tarea 4.2 — gráficos accesibles

- Objetivo: CSS/SVG con equivalentes textuales.
- Archivos: `frontend/js/dashboard.js`, HTML, CSS, UI y tests.
- Validación: `uv run pytest tests/test_static.py tests/test_dashboard.py -q`.
- Aceptación: cada visualización tiene tabla o texto equivalente y funciona por teclado.
- Commit: `feat: visualizar estadísticas accesibles`.
- Dependencias: T4.1.
- Credenciales: no.

### Tarea 4.3 — UI final de recomendaciones

- Objetivo: separar claramente datos Google, personales y guardados.
- Archivos: frontend de recomendaciones, UI/CSS y tests.
- Tests: etiquetas, atribución, datos faltantes y modo degradado.
- Validación: `uv run pytest tests/test_recommendations.py tests/test_static.py -q`.
- Aceptación: denominaciones honestas, factores explicados y atribución correcta.
- Commit: `feat: completar recomendaciones y novedades`.
- Dependencias: T2.6, T2.7 y T4.1.
- Credenciales: no para tests.

## CHECKPOINT 4 — interfaz completa

Ejecutar suite y navegador local a 320, 768 y 1440 px; mostrar evidencia, diff, commits y estado. Detenerse y esperar aprobación para Fase 5.

## 7. Fase 5 — cierre

### Tarea 5.1 — regresión y navegador

- Objetivo: verificación integral reproducible.
- Archivos: tests y `docs/browser-checklist-v2.md`.
- Verificaciones: 320/768/1440, teclado, consola, degradación, dos usuarios y fallback.
- Validación:

  ```bash
  uv run pytest -q
  uv run python -m compileall backend
  uv run python -m backend.migrations verify --database data/coffee_atlas.db
  git diff --check
  ```

- Aceptación: suite verde y checklist reproducible.
- Commit: `test: verificar coffee atlas v2 de punta a punta`.
- Dependencias: Fases 1–4 aprobadas.

### Tarea 5.2 — documentación e instrucciones

- Objetivo: cerrar documentación y reglas operativas.
- Archivos: `README.md`, `docs/verification-v2.md`, `AGENTS.md`, `backend/AGENTS.md`, `frontend/AGENTS.md` y skill de preentrega.
- Validación: `uv run pytest -q`, `git diff --check`, `git status --short --branch`.
- Aceptación: V1 congelada, diferencias explicadas y secretos ausentes.
- Commit: `docs: cerrar entrega de coffee atlas v2`.
- Dependencias: T5.1.

## CHECKPOINT 5 — entrega

Ejecutar la skill de preentrega, mostrar informe, diff final, commits y estado. Detenerse; no publicar ni realizar otras acciones sin autorización.

## 8. Estrategia de tests

### Unitarios

- sesiones, CSRF y expiraciones;
- Haversine;
- score de recomendaciones;
- validación CABA y TTL;
- MIME, dimensiones y nombres de archivos;
- agregados del dashboard.

### Integración

- SQLite temporal y dos usuarios;
- Auth0 y Places falsos;
- bloqueo de toda salida de red;
- migración, backup, verify y restore sobre copias temporales;
- persistencia entre instancias;
- propiedad de cafeterías, visitas y fotos.

### Navegador

- registro/login/logout real sólo tras su checkpoint;
- mapa y Google real sólo tras su checkpoint;
- permisos de geolocalización concedido, rechazo, timeout y fallback;
- sincronización tarjeta/marcador;
- uploads, dashboard, tablas, atribución y modo degradado;
- consola limpia.

Los 25 casos V1 se mantienen o adaptan a una sesión autenticada y sus cambios de contrato se documentan.

## 9. Commits previstos

La rama de trabajo es `codex/coffee-atlas-v2`. Ningún commit está autorizado antes de completar CHECKPOINT 0 y recibir una nueva aprobación.

1. `docs: definir especificación y plan de coffee atlas v2`
2. `chore: preparar configuración segura de v2`
3. `feat: agregar sesiones locales opacas`
4. `feat: integrar auth0 mediante un adaptador verificable`
5. `feat: aislar el atlas por usuario`
6. `feat: agregar migración respaldada desde v1`
7. `feat: incorporar experiencia de sesión`
8. `test: verificar autenticación y reconciliación reales`
9. `feat: agregar adaptador para places api new`
10. `feat: validar ubicaciones dentro de caba`
11. `feat: agregar domicilios y ubicaciones verificadas`
12. `feat: incorporar mapa y geolocalización efímera`
13. `feat: ordenar cafeterías por cercanía`
14. `feat: agregar recomendaciones determinísticas`
15. `feat: completar experiencia geográfica sin red`
16. `test: verificar integración real con google maps`
17. `feat: registrar historial de visitas`
18. `feat: agregar fotografías privadas de visitas`
19. `feat: completar experiencia de visitas`
20. `feat: agregar dashboard personal`
21. `feat: visualizar estadísticas accesibles`
22. `feat: completar recomendaciones y novedades`
23. `test: verificar coffee atlas v2 de punta a punta`
24. `docs: cerrar entrega de coffee atlas v2`

## 10. Acciones automáticas y manuales

El agente puede crear `.env.example`, implementar código/tests/mocks, ejecutar validaciones locales sin red, documentar instrucciones, comprobar integraciones ya configuradas y migrar sólo con la autorización específica correspondiente.

El usuario realiza creación de cuentas, aceptación de términos, facturación, medios de pago, obtención de identificadores y carga local de credenciales. Los secretos no se solicitan por chat, no se imprimen y no se versionan.

## 11. Estimaciones orientativas

| Categoría | Estimación |
|---|---:|
| Esfuerzo humano equivalente | 58–76 horas |
| Ejecución asistida por Codex | 24–36 horas activas |
| Configuración manual Auth0 | 30–60 minutos |
| Configuración manual Google Cloud | 45–90 minutos |
| Verificación humana/checkpoints | 5–8 horas |
| Contingencia | 20–30% adicional |

Son orientaciones, no garantías, y no incluyen tiempos de espera por aprobaciones.

## 12. Riesgos y criterio de recorte

Riesgos principales: revocación Auth0 externa no inmediata, cuotas/costos de Nearby Search, vencimiento de coordenadas, restricciones de persistencia Google, origen o claves mal configurados, privacidad, crecimiento local y una base inesperada durante migración.

Orden de recorte:

1. animaciones y adornos;
2. cantidad/frecuencia de candidatos;
3. elementos visuales secundarios;
4. bloque externo de recomendaciones si el SKU no resulta aceptable.

Nunca se recortan aislamiento, CSRF, sesiones, backup/restauración, TTL, validación CABA, seguridad de uploads, tests sin red ni accesibilidad esencial. Ante una desviación material, se detiene la fase y se solicita decisión.
