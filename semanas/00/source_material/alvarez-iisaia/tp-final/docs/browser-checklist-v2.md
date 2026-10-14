# Checklist de navegador — Coffee Atlas V2

Este recorrido valida la interfaz V2 sin utilizar la base de desarrollo, el
archivo `.env`, credenciales reales ni servicios externos. Debe ejecutarse con
SQLite, uploads, Auth0 y Places temporales o falsos.

## Preparación aislada

1. Crear una base SQLite y un directorio de uploads en una carpeta temporal.
2. Inyectar un proveedor Auth falso con dos identidades distintas.
3. Inyectar un proveedor Places falso con Details y Nearby determinísticos.
4. No configurar claves Google: esto permite comprobar también el modo
   degradado.
5. Iniciar el servidor sólo en `http://127.0.0.1:8000`, sin access log.
6. Confirmar que `data/coffee_atlas.db`, `data/uploads/` y `.env` no cambian.

## Sesión y aislamiento

- La portada anónima ofrece **Iniciar sesión** y **Crear cuenta**.
- El login falso crea una sesión local y muestra la identidad esperada.
- El logout vuelve a la portada anónima e invalida la sesión local.
- Una segunda identidad recibe un atlas vacío, total `0` y ninguna cafetería
  de la primera identidad.
- Las pruebas automáticas complementarias verifican `401`, CSRF, expiraciones y
  acceso cruzado con respuesta `404`.

## Contenido y estados

- Los contadores, dashboard, filtros y siete cafeterías temporales coinciden.
- Cada gráfico posee una tabla o alternativa textual.
- Las cafeterías sin imagen muestran el fallback **Sin fotografía**.
- Sin claves Google, mapa y autocompletado explican que no están disponibles.
- El domicilio local sigue visible en modo degradado.
- Nearby falso muestra dos recomendaciones y separa:
  - datos actuales y atribución de Google Maps;
  - cálculo determinístico personal;
  - datos que se guardarían localmente.
- Los estados vacío, carga, error y archivo faltante están cubiertos además
  por la suite automática.

## Accesibilidad y teclado

- Recorrer enlaces, campos, radios, selects y botones con `Tab`.
- Abrir **Agregar cafetería**: el foco debe entrar en el primer campo.
- Presionar `Escape`: el diálogo debe cerrar y devolver el foco al botón que lo
  abrió.
- Confirmar labels visibles, foco perceptible, orden natural y regiones
  `aria-live`.
- Confirmar que tarjetas y estados no dependen sólo del color.
- Verificar que las tablas accesibles contienen los mismos valores que los
  gráficos.

## Responsive y consola

Para cada viewport, revisar toda la página, medir `scrollWidth`, comprobar que
ningún control interactivo quede fuera de la ventana y consultar errores y
advertencias de consola.

| Viewport | Resultado esperado |
|---|---|
| 320 × 900 | Una columna, `scrollWidth=320`, sin overflow horizontal |
| 768 × 900 | Dos columnas de cafeterías, sin overflow horizontal |
| 1440 × 1000 | Tres columnas de cafeterías, sin overflow horizontal |

La consola debe quedar sin errores ni advertencias de la aplicación.

## Evidencia del 14 de octubre de 2026

- 320 px: `scrollWidth=320`, siete tarjetas, cero controles fuera del viewport.
- 768 px: `scrollWidth=768`, grilla de cafeterías en dos columnas y cero
  controles fuera del viewport.
- 1440 px: `scrollWidth=1440`, grilla de cafeterías en tres columnas y cero
  controles fuera del viewport.
- Diálogo: foco inicial en `cafe-name`; al cerrar con `Escape`, foco restaurado
  en `add-cafe`.
- Recomendaciones: dos resultados falsos, ambos con bloques Google, personal y
  guardado claramente separados.
- Segunda identidad falsa: total `0`, cero tarjetas y estado vacío visible.
- Consola: cero errores y cero advertencias.

## Verificaciones deliberadamente separadas

La autenticación Auth0 y Google reales ya tienen checkpoints manuales propios.
Esta lista no los repite ni consume cuota. La verificación de
`data/coffee_atlas.db` tampoco forma parte de este recorrido: requiere una
autorización independiente para operar sobre datos reales.
