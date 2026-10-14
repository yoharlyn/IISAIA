# Checklist de navegador — Coffee Atlas

Usar con la aplicación iniciada mediante:

```bash
uv run fastapi dev backend/main.py
```

Abrir `http://127.0.0.1:8000` y recorrer los pasos en orden. La columna
“Evidencia 2026-10-13” registra la ejecución realizada durante la implementación.

| Verificación | Resultado esperado | Evidencia 2026-10-13 |
|---|---|---|
| Carga inicial | Siete tarjetas y contadores 7/4/3/3 | Correcto |
| 320 px | Una columna, sin scroll horizontal | Correcto: `scrollWidth=320` |
| 768 px | Dos columnas, sin desborde | Correcto: dos columnas |
| 1440 px | Tres columnas, sin desborde | Correcto: tres columnas |
| Buscar “Bruma” + favoritas | Sólo Bruma Café | Correcto |
| Limpiar filtros | Regresan las siete tarjetas | Correcto |
| Alta | Formulario crea una tarjeta y actualiza stats | Correcto con Prisma Café |
| URL rota | Aparece “Sin fotografía” | Correcto |
| Edición | Cambian nombre y estado, se conservan los otros campos | Correcto |
| Favorito | Cambia texto/estado del botón y contador | Correcto |
| Abrir eliminación y cancelar | El registro permanece y el foco vuelve a Eliminar | Correcto |
| Escape en formulario | Cierra y devuelve foco a Agregar cafetería | Correcto |
| Reinicio del servidor | El registro creado y editado continúa | Correcto |
| Servidor detenido | Mensaje de conexión y botón “Reintentar” | Correcto |
| Recuperación | Al reiniciar y reintentar vuelven las siete tarjetas | Correcto |
| Consola | Sin errores ni warnings | Correcto |

## Comprobación manual destructiva restante

Para no ejecutar una eliminación local irreversible mediante la interfaz sin una
confirmación humana en el momento, la verificación visual llegó hasta abrir el
diálogo y cancelar. El endpoint `DELETE` fue verificado por pytest y por una
solicitud HTTP real que devolvió `204`.

Antes de entregar, si se desea observar el último paso manual:

1. Crear una cafetería temporal desde la interfaz.
2. Pulsar “Eliminar”.
3. Confirmar que el diálogo nombra la cafetería correcta.
4. Pulsar “Eliminar definitivamente”.
5. Confirmar que la tarjeta desaparece y baja el contador total.
6. Reiniciar el servidor y confirmar que no reaparece.

## Estados de error reproducibles

1. Abrir la aplicación y esperar la carga correcta.
2. Detener el servidor.
3. Pulsar “Aplicar filtros” o intentar guardar un formulario ya abierto.
4. Confirmar el mensaje: “No pudimos conectar con Coffee Atlas. Revisá que el
   servidor esté activo.”
5. Reiniciar el servidor y usar “Reintentar”.
