# Plan aprobado — Coffee Atlas V3

Este documento fija el orden incremental aprobado para Coffee Atlas V3. Los
documentos V1 y V2 permanecen congelados. Las diferencias que surjan durante la
implementación se registrarán en la documentación y evidencia V3, sin reescribir
planes históricos.

## 1. Autorizaciones y reglas de ejecución

- Rama exclusiva: `codex/coffee-atlas-v3`.
- Cada fase termina en un checkpoint y requiere aprobación para continuar.
- Ante una validación fallida se detiene la fase y se informa la causa.
- No se realiza push, merge con `main` ni uso de `--force`.
- Base, uploads, `.env`, claves y tokens reales no se usan en tests.
- No se abren ni imprimen secretos.
- Auth0 y Google reales requieren checkpoints y autorizaciones separados.
- Migraciones y verificaciones automatizadas usan primero bases temporales.
- Ninguna operación sobre la base real se infiere de la aprobación de este plan.
- Los documentos históricos `spec.md`, `plan.md`, `spec-v2.md` y `plan-v2.md`
  no se modifican.

## 2. Decisiones cerradas

- Se elimina sólo el bloque visual duplicado; `GET /api/stats` se conserva por
  compatibilidad.
- El gráfico continúa con SVG, CSS y JavaScript nativos.
- El GeoJSON oficial versionado es la fuente interna de barrios.
- Los valores históricos no reconocidos se muestran separados y no se migran.
- El buscador de Places es el recorrido accesible principal del mapa; los POI
  son complementarios.
- Mapa y recomendaciones usan el mismo formulario y `POST /api/cafes`.
- Los endpoints V2 de recomendaciones se conservan por compatibilidad.
- La descripción opcional se persiste como `NULL` y requiere esquema V4.
- No se agregan frameworks, Node, bundlers ni librerías gráficas al producto.
- UI/UX Pro Max y 21st UI Review tienen un checkpoint de instalación separado.
- 21st.dev se limita a `21st-ui-review`, sin CLI, MCP ni generación remota.

## 3. Fase V3.0 — documentación y evaluación de skills

### Objetivo

Fijar el contrato y el orden de trabajo V3 sin modificar la aplicación.

### Archivos

- `docs/spec-v3.md`
- `docs/plan-v3.md`

### Cambios

- Registrar alcance, compatibilidad, seguridad, migración y criterios de
  aceptación.
- Incorporar el recorrido accesible mediante buscador de Places.
- Separar instalación de skills, migración temporal y cualquier operación real.
- Documentar que los metadatos del GeoJSON se consignan sólo si pueden
  comprobarse.

### Verificación

```bash
git diff --check
git diff --stat
git status --short --branch
```

También se comparan hashes o diffs de los cuatro documentos históricos con el
estado anterior a esta fase.

### Riesgos

- Alterar accidentalmente documentación histórica.
- Mezclar la aprobación documental con permisos para instalar o ejecutar.

### Criterio de cierre

Sólo existen los dos documentos V3 como cambios del árbol y las validaciones de
texto son correctas.

### Checkpoint

**CHECKPOINT V3.0 — DOCUMENTACIÓN CREADA**

Detenerse y esperar aprobación. No instalar skills ni iniciar V3.1.

### Commit propuesto

`docs: definir especificación y plan de coffee atlas v3`

## 4. Checkpoint independiente — instalación de skills

Este checkpoint ocurre únicamente después de una autorización expresa posterior
a V3.0. No forma parte automática de ninguna fase funcional.

Antes de instalar se presentará para cada repositorio:

- commit SHA exacto fijado;
- licencia y fuente;
- manifest completo de archivos a copiar;
- destino dentro del proyecto;
- referencias de rutas que requieran adaptación;
- comandos que necesitarían red;
- scripts o dependencias incluidas, sin ejecutarlas.

No se realizará red adicional ni se ejecutarán scripts de las skills hasta
obtener autorización sobre ese manifest.

### UI/UX Pro Max

Destino previsto, sujeto al manifest aprobado:

```text
.codex/skills/ui-ux-pro-max/
├── SKILL.md
├── data/
└── scripts/
```

La instalación será local al proyecto y sin `sudo`. Se priorizará el instalador
de skills de Codex con un `--ref` fijado y sin agregar Node o `node_modules` al
proyecto. Antes de ejecutar cualquier script Python se comprobarán imports,
rutas relativas y ausencia de acceso de red. Si el paquete fijado no resulta
autocontenido, la instalación se detendrá.

Uso previsto: referencia para tokens, dashboard, gráficos, formularios,
accesibilidad y responsive. Sus sugerencias no autorizan Tailwind, React,
fuentes remotas ni cambios de identidad.

### 21st UI Review

Destino previsto:

```text
.codex/skills/21st-ui-review/
└── SKILL.md
```

Se usarán sólo sus criterios textuales de revisión. No se instalarán ni
ejecutarán CLI, MCP, cuenta, API key, generación, componentes React o comandos
`21st review`. No se crearán `.21st/`, `components.json`, `components/ui`,
`package.json`, lockfiles ni `node_modules`.

### Cierre del checkpoint

Manifest y rutas coinciden con lo aprobado; no se ejecutó código remoto y el
diff contiene únicamente los archivos de skills autorizados.

### Commit propuesto

`chore: agregar referencias locales de diseño aprobadas`

## 5. Fase V3.1 — dashboard y gráfico de visitas

### Objetivo

Eliminar la duplicación visual y convertir la serie mensual en una visualización
interpretable y accesible.

### Archivos probablemente afectados

- shell y módulos `app`, `ui` y `dashboard` del frontend;
- CSS principal;
- tests estáticos, de cafeterías y dashboard.

### Cambios funcionales

- Retirar `stats-grid`, su renderizado y la llamada V3 a `getStats`.
- Conservar endpoint, schema y tests de `/api/stats`.
- Agregar eje Y entero, líneas guía, meses, valores, leyenda y resumen textual.
- Mantener tabla equivalente con visitas y acumulado.
- Agregar estado vacío y escala segura para pocos datos.

### Tests necesarios

- El shell no contiene el bloque duplicado.
- El frontend no solicita stats durante su carga normal.
- `/api/stats` conserva autenticación, aislamiento y contrato.
- Doce meses ordenados, cambio de año, ceros, un dato y máximos repetidos.
- SVG, tabla, resumen, leyenda y estado vacío expresan los mismos datos.
- Navegador y teclado a 320, 768 y 1440 px.

### Riesgos

- Solapamiento de etiquetas en pantallas pequeñas.
- Escala engañosa con valores bajos.
- Regresión de actualizaciones tras crear visitas.

### Criterio de cierre

Existe un único dashboard, no se pierde información y gráfico, texto y tabla son
coherentes.

### Checkpoint

Ejecutar tests afectados, suite offline, compilación, navegador, diff y estado.

### Commit propuesto

`feat: simplificar dashboard y mejorar gráfico de visitas`

## 6. Fase V3.2 — catálogo oficial de barrios

### Objetivo

Ofrecer los 48 barrios oficiales en forma consistente sin perder acceso a datos
históricos.

### Archivos probablemente afectados

- módulo geográfico o nuevo catálogo backend;
- ruta de catálogo y capa API del navegador;
- filtros, dashboard y tests geográficos/API/estáticos.

### Cambios funcionales

- Derivar y validar el catálogo desde el GeoJSON versionado.
- Centralizar nombres de presentación y aliases comprobados.
- Exponer 48 barrios oficiales y valores históricos del propietario.
- Ordenar con locale español.
- Canonicalizar agrupación y filtros sin reescribir SQLite.
- Documentar sólo fuente, fecha, licencia y versión comprobables.

### Tests necesarios

- Exactamente 48 nombres únicos y ordenados.
- Toda feature del GeoJSON tiene correspondencia.
- Variantes comprobadas de acentos y mayúsculas se agrupan.
- Valores no canónicos quedan en la sección histórica.
- Históricos de otro usuario no se exponen.
- Altas nuevas reciben barrio canónico del backend.

### Riesgos

- Alias ambiguos como `Centro`.
- Diferencias entre nombre del dataset y nombre de presentación.
- División incorrecta de conteos históricos.

### Criterio de cierre

Los 48 barrios oficiales están disponibles y ningún registro existente queda
imposible de filtrar.

### Checkpoint

Tests geográficos, API, frontend, suite y navegador, sin usar Google real.

### Commit propuesto

`feat: unificar catálogo oficial de barrios de caba`

## 7. Fase V3.3 — alta unificada desde Places

### Objetivo

Compartir un recorrido seguro y accesible de alta para mapa, recomendaciones y
formulario general.

### Archivos probablemente afectados

- adaptador Places, schemas y rutas de preparación;
- módulos de mapa, Places, recomendaciones, formulario y API;
- tests de Places, ubicaciones, recomendaciones, escritura y frontend.

### Cambios funcionales

- Incorporar `displayName` a la field mask mínima de Details.
- Agregar `POST /api/places/{place_id}/prepare-cafe`.
- Detectar duplicados del propietario sin filtrar datos ajenos.
- Conservar endpoints V2 como alias o compatibilidad.
- Incorporar un buscador de Places accesible junto al mapa.
- Permitir selección complementaria de POI con Place ID.
- Mostrar panel de selección con nombre, dirección, barrio y atribución.
- Abrir el mismo formulario desde mapa y recomendaciones.
- Precargar dirección canónica sin repetir el autocomplete.
- Persistir sólo mediante confirmación y `POST /api/cafes`.

El buscador es el recorrido principal para teclado y tecnologías de asistencia.
La interacción visual con POI nunca será el único medio de selección.

### Tests necesarios

- Details devuelve y valida nombre, dirección y Place ID canónicos.
- CABA, fuera de CABA, proveedor caído y respuesta inválida.
- Duplicado propio y aislamiento entre dos usuarios.
- Recomendación precarga dirección sin nueva búsqueda.
- Buscador usable por teclado y selección anunciada.
- POI válido, punto vacío, cancelación y ausencia de guardado automático.
- Manipulación de dirección, nombre, barrio y Place ID.
- Foco, retorno de foco, `aria-live`, carga y error.

### Riesgos

- Diferencias entre eventos de POI y Places API (New).
- Consumo adicional de Details.
- Foco incorrecto entre mapa, panel y diálogo.
- Duplicación accidental entre rutas de guardado.

### Criterio de cierre

Mapa y recomendaciones abren el mismo formulario; el buscador ofrece el flujo
accesible completo y ninguna selección guarda automáticamente.

### Checkpoint

Proveedores falsos, tests afectados, suite, compilación y navegador degradado.
Google real sólo se verifica con autorización separada.

### Commit propuesto

`feat: unificar alta de cafeterías desde places`

## 8. Fase V3.4 — descripción opcional y esquema V4

### Objetivo

Permitir cafeterías sin descripción en toda la pila y migrar el esquema de forma
explícita y recuperable.

### Archivos probablemente afectados

- modelos, schemas y migraciones;
- serialización, formulario y tarjetas;
- tests de escritura, lectura y migraciones.

### Cambios funcionales

- Aceptar `None` y normalizar texto vacío a `None`.
- Retirar obligatoriedad del textarea.
- Ajustar lectura, edición y fallback visual.
- Elevar `SCHEMA_VERSION` a 4.
- Recrear `cafes` de forma transaccional conservando todas sus restricciones y
  relaciones.
- Rechazar startup sobre V3 pendiente sin escribir.

### Tests necesarios

- Alta sin campo, con `null`, vacío y límite de 600 caracteres.
- Patch para agregar, cambiar y quitar descripción.
- Lectura y tarjeta sin descripción.
- Upgrade V3→V4 sobre copias temporales.
- Conservación de filas, IDs, FKs, índices y unicidad.
- Rollback simulado, idempotencia, `status` y `verify` temporales.
- Startup fail-closed sin modificar la base pendiente.

### Restricción de migración

La implementación y toda verificación inicial se ejecutan únicamente con bases
temporales. No se ejecutan `backup`, `upgrade`, `restore`, `verify` ni ninguna
otra operación sobre la base real sin una autorización específica posterior,
con el servidor detenido y un procedimiento de evidencia aprobado.

### Riesgos

- SQLite requiere recreación de tabla.
- Omisión accidental de un índice, constraint o FK.
- Clasificación incorrecta de versiones anteriores.

### Criterio de cierre

La migración temporal, rollback e idempotencia están probados; la base real no
fue inspeccionada ni modificada.

### Checkpoint

Presentar evidencia temporal y detenerse antes de cualquier operación real.

### Commit propuesto

`feat: admitir descripciones opcionales con esquema v4`

## 9. Fase V3.5 — sistema visual y validación final

### Objetivo

Aplicar un sistema visual coherente y cerrar V3 con evidencia reproducible.

### Archivos probablemente afectados

- CSS principal y shell HTML;
- módulos de UI de las superficies ajustadas;
- checklist, evidencia y README V3.

### Cambios funcionales

- Completar tokens semánticos de color, tipografía, espacio, radios y sombra.
- Unificar botones, campos, tarjetas, paneles, tablas y diálogos.
- Mejorar navegación, dashboard, mapa, recomendaciones y estados.
- Preservar portada, identidad, Términos y Privacidad.
- Mantener foco visible, reduced motion y ausencia de overflow real.

### Tests y verificaciones

```bash
UV_CACHE_DIR=/private/tmp/coffee-atlas-uv-cache uv run --offline pytest -q
UV_CACHE_DIR=/private/tmp/coffee-atlas-uv-cache uv run --offline python -m compileall -q backend
git diff --check
```

Navegador temporal:

- 320, 768 y 1440 px;
- teclado completo y lector de pantalla cuando esté disponible;
- foco, diálogos y retorno de foco;
- carga, vacío, error, éxito y confirmación;
- mapa degradado, buscador, recomendaciones y duplicados;
- dos usuarios aislados;
- consola limpia y sin overflow horizontal.

### Riesgos

- Reducir contraste al embellecer componentes.
- Romper densidad o legibilidad móvil.
- Cambiar identidad o contenido sin justificación funcional.

### Criterio de cierre

Suite, compilación, navegador y skill local de preentrega verdes; evidencia V3
sanitizada y documentos históricos intactos.

### Checkpoint

Mostrar informe final, diff, commits y estado. No publicar ni fusionar.

### Commits propuestos

- `feat: consolidar sistema visual de coffee atlas`
- `test: verificar coffee atlas v3 de punta a punta`
- `docs: cerrar entrega de coffee atlas v3`

## 10. Estrategia global de pruebas

### Unitarias

- canonicalización y catálogo de barrios;
- escala y datos del gráfico;
- preparación de Place Details;
- normalización de descripción;
- detección de duplicados.

### Integración

- SQLite y uploads temporales;
- dos propietarios;
- Auth y Places falsos;
- CSRF, Origin y `404` cruzados;
- esquema V4, rollback e idempotencia;
- cero tráfico de red.

### Navegador

- buscador de Places accesible y POI complementario;
- formulario unificado desde tres orígenes;
- dashboard y tabla equivalentes;
- barrios oficiales e históricos;
- estados degradados y resoluciones requeridas.

## 11. Riesgos y límites

- Cambios de contrato o eventos de Google Maps pueden requerir ajustar el flujo
  complementario de POI; el buscador accesible no depende de ese recorrido.
- La cuota de Details se controla evitando llamadas automáticas innecesarias.
- La canonicalización no debe reinterpretar valores históricos ambiguos.
- La migración nullable exige especial cuidado al recrear SQLite.
- Las skills de terceros cambian con el tiempo; por eso se fijan por SHA y se
  auditan antes de instalar o ejecutar.
- La revocación Auth0 externa, el TTL de coordenadas y la escala local de SQLite
  conservan los límites deliberados de V2.
