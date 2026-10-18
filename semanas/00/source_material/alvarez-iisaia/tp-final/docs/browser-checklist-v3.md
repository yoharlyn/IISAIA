# Checklist de navegador — Coffee Atlas V3

Este recorrido valida V3 sin usar `.env`, base, uploads, Auth0 ni Google reales.
Debe ejecutarse en `http://127.0.0.1:8000` con recursos temporales y eliminarse
por completo al finalizar.

## Preparación aislada

1. Crear una carpeta temporal y verificar su ruta absoluta.
2. Crear allí una base SQLite nueva en esquema V4 y un directorio de uploads.
3. Inyectar dos identidades falsas con colecciones diferentes.
4. Inyectar Place Details y Nearby determinísticos, sin tráfico de red.
5. Servir un adaptador de mapa falso local; ejecutar después otra instancia sin
   claves para el modo degradado.
6. No cargar `.env` ni depender de la ruta de base por defecto.
7. Confirmar antes y después que la base y los uploads reales no se modificaron.

## Navegación y estructura

- `Tab` enfoca **Saltar al contenido**; `Enter` mueve foco a `main`.
- Marca, sesión y acciones se distinguen sin competir en móvil.
- Las anclas Descubrir, Mis cafeterías, Mapa y Dashboard siguen ese mismo orden
  en menú y DOM, con `scroll-margin`, foco programático y headings coherentes.
- La portada continúa reconocible y el hero no desplaza el contenido esencial.
- Footer, Términos y Privacidad son alcanzables con teclado.

## Dashboard

- Existe un solo **Dashboard personal**.
- Los KPI muestran visitas, visitadas, pendientes y favoritas.
- El gráfico presenta doce meses, eje cuantitativo entero, líneas guía, valores,
  contexto y resumen textual.
- Los ceros no se repiten sobre los meses; el eje conserva su referencia cero y
  los ticks enteros son únicos.
- La tabla equivalente coincide mes por mes y conserva el acumulado.
- El contenedor local permite desplazar gráfico o tabla en 320 px sin producir
  overflow del documento.
- Cero visitas produce un estado vacío comprensible.

## Barrios y filtros

- El panel de búsqueda y filtros forma parte de **Mis cafeterías** y aparece una
  sola vez antes de la grilla.
- **Todos los barrios** es la selección inicial.
- El grupo **Barrios oficiales** contiene exactamente 48 opciones únicas y
  ordenadas con el criterio español de la aplicación.
- **Valores históricos** aparece sólo para la identidad que los posee.
- Un histórico sigue siendo filtrable.
- Búsqueda, estado, favoritas, aplicar y limpiar funcionan con teclado.
- Un filtro sin resultados muestra el estado vacío y permite limpiarlo.

## Mapa y alta unificada

- El buscador de cafetería tiene nombre accesible y funciona con teclado.
- Una selección válida prepara nombre, dirección y barrio sin persistir.
- Un POI falso con Place ID produce la misma selección preparada.
- Un clic sin Place ID no ofrece alta.
- La acción **Agregar a mis cafeterías** es explícita; seleccionar no guarda.
- Un duplicado propio muestra **Ya está en tu atlas** y permite abrir su ficha.
- El mismo Place ID guardado por otra identidad no revela ese dato.
- Alta general, mapa, POI y recomendación abren el mismo diálogo.
- Nombre y dirección canónicos están precargados y no se repite autocomplete.
- Descripción se anuncia como opcional y puede quedar vacía.
- Mientras guarda, la acción se deshabilita; éxito, error y duplicado se anuncian.
- Cancelar no persiste y devuelve el foco al disparador.

## Recomendaciones, colección y visitas

- La lista muestra cuatro recomendaciones por página, con Anterior, Siguiente e
  indicador Página X de Y.
- Los casos 0, 1, 4, 5 y 19 conservan todos los resultados; una nueva búsqueda
  reinicia en página 1 y cambiar de página no consulta nuevamente al proveedor.
- Los límites deshabilitan el botón correspondiente, mantienen foco útil y
  anuncian la página mediante `aria-live`.
- La recomendación falsa separa datos Google, cálculo personal y datos a guardar.
- La dirección preparada aparece antes de confirmar.
- El alta final sin descripción muestra el fallback **Sin descripción.**
- Las tarjetas con y sin descripción mantienen igual jerarquía y acciones visibles.
- **Visitas** tiene prioridad, **Editar** es secundaria y **Eliminar** conserva
  menor peso hasta su confirmación.
- El historial muestra nota, ratings y fotografía temporal privada.
- Diálogo de visitas, editor y upload caben en 320 px con scroll localizado.
- Cerrar diálogos restaura foco al botón de origen.

## Estados y modo degradado

- Carga usa mensajes y `aria-busy`.
- Vacío diferencia colección sin datos de filtros sin resultados.
- Errores se presentan cerca del contexto y mediante alertas o regiones vivas.
- Confirmaciones se anuncian sin depender sólo del color.
- Sin claves Google:
  - mapa: **Mapa no disponible: Google Maps todavía no está configurado.**;
  - alta: explica que no se pueden agregar ubicaciones nuevas;
  - domicilio: explica que no puede verificarse;
  - buscador del mapa: explica que requiere Google Maps.
- Las funciones locales continúan disponibles y la consola permanece limpia.

## Accesibilidad

- Recorrer todos los enlaces, campos, radios, selects y botones con teclado.
- Foco visible con contorno y separación doble.
- Labels y ayudas permanecen próximos al campo correspondiente.
- Los controles propios visibles tienen un objetivo mínimo de 44×44 px.
- Estados usan texto, forma e icono cuando corresponde, no sólo color.
- `aria-live`, `aria-busy` y `role="alert"` anuncian cambios importantes.
- El gráfico tiene título, descripción y tabla equivalente.
- `prefers-reduced-motion: reduce` elimina smooth scroll y reduce transiciones.
- No se modifica el DOM interno de componentes Google.

## Responsive y consola

Medir `document.documentElement.scrollWidth`, revisar la página completa y
consultar consola en cada viewport.

| Viewport | Composición esperada |
|---|---|
| 320 × 900 | encabezado en dos filas, KPI 2×2, una columna, mapa apilado |
| 768 × 900 | KPI 2×2, tarjetas en dos columnas, mapa apilado |
| 1440 × 1000 | máximo 1180 px, KPI 4×1, tres columnas, mapa y descubrir 4/8 |

No se admite overflow horizontal del documento ni `overflow-x: hidden` para
ocultarlo. Las filas incompletas no deben crear grandes vacíos.

## Páginas legales

- Términos y Privacidad tienen un único `h1`, secciones con `h2`, enlace de
  retorno y footer.
- Contenido legal sustantivo intacto.
- Teclado, foco, contraste y ausencia de overflow a 320 y 1440 px.

## Evidencia final aprobada el 18 de octubre de 2026

- 320 px: `clientWidth=320`, `scrollWidth=320`, KPI `144px 144px`, una columna,
  mapa apilado, diálogo de visitas de `282px` dentro del viewport.
- 768 px: `clientWidth=768`, `scrollWidth=768`, KPI 2×2, colección en dos
  columnas de `356px` y mapa apilado.
- 1440 px: `clientWidth=1440`, `scrollWidth=1440`, contenido de `1180px`, KPI
  4×1, colección en tres columnas y composiciones 4/8.
- En los tres anchos: sin overflow horizontal.
- Buscador por teclado: Place falso preparado y acción explícita visible.
- POI: **Faro Tostadores** preparado sin guardado automático.
- Duplicado propio: **Bruma Café**, **Abrir ficha en mi atlas**.
- Recomendación: **Cauce Café**, dirección canónica precargada.
- Alta sin descripción: `201`, confirmación visible y fallback en tarjeta.
- Cancelación: foco devuelto al botón de recomendación o mapa correspondiente.
- Segunda identidad: una colección distinta, 48 barrios, cero históricos ajenos
  y duplicado de la primera identidad no revelado.
- Historial: nota, caption y fotografía temporal; endpoint de imagen `200
  image/jpeg`.
- Modo degradado: cuatro mensajes específicos, mapa `unavailable` y sin
  overflow.
- Términos y Privacidad: headings correctos y sin overflow a 320 px.
- Consola: cero errores y cero warnings de la aplicación en las capturas finales.
- La usuaria aprobó visualmente el orden, los filtros integrados, el gráfico y la
  paginación de V3.6.

Las interacciones POI, cancelación y retorno de foco son evidencia manual de
navegador. No existen tests E2E persistentes ni una dependencia Node para ellas;
las pruebas unitarias y de integración cubren los contratos subyacentes.

## Limpieza obligatoria

1. Detener el servidor temporal.
2. Restablecer el viewport del navegador.
3. Eliminar base, uploads, adaptador, harness y cachés temporales.
4. Confirmar que no hay procesos escuchando en `127.0.0.1:8000`.
5. Confirmar staging limpio y ausencia de cambios fuera de la documentación V3.
