# Coffee Atlas V3 — especificación

## 1. Producto y alcance

Coffee Atlas V3 evoluciona Coffee Atlas V2 para corregir inconsistencias
funcionales, simplificar recorridos y consolidar una interfaz más profesional,
sin reemplazar innecesariamente su arquitectura.

La aplicación mantiene:

- FastAPI, SQLModel y SQLite;
- Auth0 mediante Authorization Code;
- HTML, CSS y JavaScript vanilla con módulos ES;
- Maps JavaScript API y Places API (New);
- la URL canónica exclusiva `http://127.0.0.1:8000`;
- datos personales aislados por propietario autenticado;
- ubicación actual efímera y datos locales no versionados.

No incorpora React, Vue, otros frameworks frontend, Node como dependencia del
producto, bundlers, Docker, Alembic, Geocoding API, funciones sociales,
almacenamiento cloud ni IA de producto.

`docs/spec.md`, `docs/plan.md`, `docs/spec-v2.md` y `docs/plan-v2.md` permanecen
congelados como registro histórico. Este documento define únicamente los cambios
de V3; los contratos V2 no modificados continúan vigentes.

## 2. Dashboard personal único

La interfaz autenticada muestra un solo grupo de indicadores: el **Dashboard
personal**.

- Se elimina de la interfaz el bloque general que repetía total, visitadas,
  pendientes y favoritas.
- El dashboard conserva visitas registradas, cafeterías visitadas, pendientes y
  favoritas, además de sus visualizaciones y listados complementarios.
- El frontend V3 deja de solicitar `GET /api/stats`.
- `GET /api/stats` permanece autenticado, aislado por propietario y cubierto por
  tests para conservar compatibilidad con el contrato V2.
- No se elimina ninguna métrica que no esté disponible en el dashboard personal.

## 3. Visitas durante los últimos doce meses

La visualización se implementa con SVG, CSS y DOM nativos. No se agrega una
dependencia gráfica.

Debe incluir:

- los doce meses cronológicos, identificados de forma visible;
- eje o referencia cuantitativa con valores enteros;
- líneas guía, leyenda y contexto suficiente para interpretar las barras;
- valores mensuales visibles cuando el espacio lo permita sin solapamientos;
- resumen textual y tabla equivalente con mes, visitas y acumulado;
- estado vacío específico cuando los doce meses no contienen visitas;
- escala mínima de cero a uno cuando existan cero o muy pocos datos;
- comportamiento correcto en cambios de año y meses sin registros;
- diseño usable a 320, 768 y 1440 px;
- semántica accesible y una representación que no dependa sólo del color.

La tabla conserva todos los valores aunque el estado esté vacío o una etiqueta
visual deba abreviarse por falta de espacio.

## 4. Catálogo canónico de barrios de CABA

La fuente interna de verdad es el recurso geográfico oficial versionado en
`backend/data/caba_neighborhoods.geojson`. El catálogo se deriva de sus features
y debe producir exactamente 48 barrios únicos.

La documentación del recurso registra exclusivamente datos comprobables:

- URL de la fuente;
- fecha comprobada de descarga o incorporación;
- licencia comprobada;
- versión local utilizada por la aplicación.

No se completan fechas, frecuencias de actualización, nombres de versiones ni
otros metadatos ausentes mediante suposiciones.

Reglas del catálogo:

- nombres de presentación canónicos y consistentes;
- orden alfabético con reglas de locale español;
- una misma función de canonicalización para validación geográfica, filtros,
  dashboard y respuestas del backend;
- altas nuevas siempre reciben el barrio calculado por los polígonos; el
  navegador no decide ni puede sustituir ese valor;
- variantes históricas equivalentes, incluidas diferencias de mayúsculas o
  acentos conocidas, se agrupan bajo el nombre canónico;
- valores históricos no reconocidos se conservan sin reescritura y aparecen en
  una sección separada del filtro;
- sólo se exponen valores históricos pertenecientes a la persona autenticada;
- no se realiza una migración de barrios sobre cafeterías existentes.

El frontend obtiene el catálogo desde el backend; no mantiene una segunda lista
manual de 48 nombres.

## 5. Preparación unificada desde Google Places

Se incorpora el endpoint:

```text
POST /api/places/{place_id}/prepare-cafe
```

Requiere sesión, CSRF y `Origin`. Consulta Place Details con una field mask
mínima, comprueba que el ID devuelto coincida, valida que la ubicación esté en
CABA y determina el barrio mediante los recursos locales.

La respuesta contiene:

- `place_id`;
- `display_name`;
- `formatted_address`;
- `neighborhood`;
- `already_saved`;
- `existing_cafe_id`, sólo si la cafetería pertenece a la persona autenticada;
- atribución `Google Maps`.

La preparación no persiste una cafetería, una ubicación ni una selección. Ante
un fallo de Places devuelve un error seguro; una ubicación fuera de CABA o una
respuesta inconsistente devuelve `422`.

El endpoint V2
`POST /api/recommendations/{place_id}/prepare-save` se conserva como alias
compatible de la misma lógica. El endpoint V2 específico de guardado permanece
disponible por compatibilidad, pero el frontend V3 deja de utilizarlo.

## 6. Alta accesible desde el mapa

La sección de mapa incorpora un buscador de Places accesible como recorrido
principal para seleccionar una cafetería. Debe ser operable con teclado, tener
nombre accesible y comunicar selección, carga, error y duplicado mediante texto
y regiones vivas.

La interacción directa con POI del mapa puede complementar el buscador cuando
Google Maps entregue un Place ID, pero nunca será el único recorrido disponible
para teclado o tecnologías de asistencia.

Después de seleccionar un lugar válido:

1. el backend prepara y valida el Place ID;
2. la interfaz muestra nombre y dirección canónicos, barrio y atribución;
3. una acción explícita **Agregar a mis cafeterías** abre el formulario común;
4. el formulario constituye la confirmación final antes de persistir.

Un clic sobre una coordenada vacía, la ubicación actual o un elemento sin Place
ID no guarda ni prepara automáticamente una cafetería. Geocoding continúa
prohibido.

Si el Place ID ya pertenece al atlas de la persona, se informa **Ya está en tu
atlas** y se ofrece localizar o editar la ficha existente. No se revelan IDs ni
datos de otras personas.

## 7. Alta desde recomendaciones

**Confirmar datos para guardar** ejecuta la preparación del Place ID y abre el
mismo formulario usado por el mapa y el alta general.

- El nombre y la dirección canónicos provienen de Place Details.
- El Place ID se conserva durante el recorrido.
- La dirección se muestra en el formulario y no debe buscarse ni escribirse de
  nuevo.
- Los datos Google actuales no se persisten como un snapshot fuera del contrato
  permitido.
- La detección de duplicados ocurre antes de abrir un alta nueva y vuelve a
  protegerse mediante la restricción de base.
- El guardado final utiliza `POST /api/cafes`.

## 8. Formulario único de cafetería

El formulario puede abrirse vacío, desde el buscador del mapa, desde un POI o
desde recomendaciones.

- Nombre y dirección se precargan cuando existe una selección validada.
- Place ID y dirección viajan al backend, que vuelve a consultar Place Details y
  no confía en los valores del navegador.
- Barrio, coordenadas, expiración y evidencia CABA provienen del backend.
- Nombre local, favorita, URL de imagen y descripción respetan sus contratos.
- El botón de envío se deshabilita mientras la mutación está en curso.
- Cancelar no persiste datos y devuelve el foco al control que inició el flujo.
- Los errores permanecen en el diálogo y se anuncian de forma accesible.

La unicidad continúa definida por `(owner_id, place_id)`. Un duplicado propio
devuelve `409`; el aislamiento y las respuestas `404` para IDs ajenos continúan
vigentes.

## 9. Descripción opcional y esquema V4

La descripción de una cafetería pasa a ser opcional en frontend, schemas,
backend, modelo, SQLite y tests.

- El valor persistido es `NULL` o texto normalizado de 1 a 600 caracteres.
- Una cadena vacía o compuesta sólo por espacios se normaliza a `NULL`.
- `CafeCreate`, `CafeUpdate`, `CafeRead` y los contratos compatibles de
  recomendaciones aceptan ausencia de descripción.
- Quitar una descripción mediante `PATCH` se representa con `null`.
- Las tarjetas muestran un fallback discreto y no dejan un espacio vacío fijo.
- Las descripciones existentes se preservan sin cambios.

SQLite pasa al esquema 4. La migración recrea `cafes` dentro de una transacción y
conserva IDs, propietarios, relaciones, timestamps, índices, restricciones,
ubicaciones y datos existentes.

La migración V4 se implementa y verifica primero exclusivamente con bases
temporales. No se ejecutan `backup`, `upgrade`, `verify`, `restore` ni otras
operaciones sobre la base real sin una autorización específica posterior y con
el servidor detenido.

El startup nunca migra automáticamente: una base V3 pendiente debe rechazarse
sin escrituras y remitir al procedimiento manual.

## 10. Sistema visual V3

La mejora visual parte de las variables CSS y componentes actuales y preserva la
identidad relacionada con el café.

El sistema reusable define:

- colores semánticos de texto, superficie, borde, acción y estados;
- escalas de tipografía, espaciado, radios y sombras;
- jerarquía consistente de títulos y textos auxiliares;
- botones primarios, secundarios, silenciosos y destructivos;
- campos, ayudas, validaciones y estados deshabilitados;
- tarjetas, paneles, tablas, badges y diálogos;
- patrones de carga, vacío, error, éxito y confirmación;
- foco visible, objetivos táctiles y reducción de movimiento.

Se revisan navegación, dashboard, gráficos, mapa, recomendaciones, formularios y
colección. La portada, el contenido funcional vigente y las páginas de Términos
y Privacidad se preservan salvo que una inconsistencia comprobada requiera un
ajuste.

No se usa `overflow-x: hidden` para ocultar defectos responsive.

## 11. Seguridad, privacidad y degradación

- Toda entidad personal continúa filtrada por `owner_id`.
- Toda mutación mantiene CSRF y validación de `Origin`.
- Auth0 y sesiones locales hasheadas conservan el contrato V2.
- La ubicación actual nunca se incorpora a URL, SQLite, logs ni storage del
  navegador.
- Place IDs pueden persistir y las coordenadas vencen a los 29 días.
- Fotos privadas continúan servidas sólo por endpoints autenticados.
- `frontend/js/api.js` sigue siendo la única capa HTTP del navegador.
- Sin Google, las funciones locales permanecen disponibles y los recorridos
  geográficos muestran un estado degradado claro.
- Los tests automatizados usan SQLite, uploads, Auth y Places temporales o
  falsos, con red bloqueada.

## 12. Criterios de aceptación V3

- Un único dashboard visible y `/api/stats` compatible.
- Gráfico mensual comprensible, accesible y responsive.
- Exactamente 48 barrios oficiales únicos y valores históricos accesibles.
- Buscador de Places accesible como recorrido principal del mapa.
- Recomendaciones y mapa reutilizan el mismo formulario.
- Ninguna selección guarda automáticamente.
- Nombre, dirección y Place ID se validan mediante Details en el backend.
- Descripción opcional en toda la pila y migración temporal probada.
- Sin dependencias de frontend nuevas ni cambio de arquitectura.
- Suite, compilación, navegador y auditoría de preentrega verdes.
- Ninguna operación sobre base o proveedores reales sin su checkpoint y
  autorización específicos.
