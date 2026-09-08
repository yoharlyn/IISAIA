# Prompts — TP 1

El desarrollo se realizó mediante 3 iteraciones en una conversación con Codex. A continuación se muestran los prompts utilizados.

---

## 1 — Prompt inicial

```
Necesito crear una página web sencilla para ingresar una fecha de nacimiento a través de sudokus.

Comportamiento:
- Para ingresar cada dígito debe hacerse a través de un sudoku. El sudoku mostrado es random y deberá estar por completar, sólo debe faltar una casilla por cada dígito (1 al 9). 
- Antes de mostrar el sudoku, debe preguntar al usuario si el dígito es cero y las opciones "sí" y "no". En caso de seleccionar "no", mostrará el sudoku, en caso de ser "sí", rellenará esa casilla con 0.

Estructura:
- <header> con el título "Ingrese su fecha de nacimiento".
- <main> un recuadro pequeño para cada dígito, un slash de separación entre los dígitos de día, mes y año, arriba de cada sección los títulos centrados: "Día", "Mes", Año. Debajo de los recuadros irá apareciendo el sudoku a resolver. Debajo del sudoku un <button> "Agregar" 

Estilo:
- Colores azules y grises.
- Fuente de letra: DM Sans

Constraints:
- Un solo archivo HTML, con el CSS en un <style> y el JS en un <script>.
- Vanilla JS, sin frameworks ni dependencias externas.
```

**Qué intentaba lograr:** crear la estructura completa de la página, definir su apariencia y establecer el funcionamiento inicial para ingresar cada dígito mediante un sudoku.

**Qué devolvió:** una página funcional en un único archivo HTML, con los campos para la fecha, la pregunta por el cero y sudokus generados al azar.

---

## 2 — Simplificar la resolución del sudoku

```
Elimina el párrafo del header.

El usuario no necesita completar todo el sudoku. Es suficiente con ingresar sólo un número en la posición correcta respetando las reglas. Con ese número que ingrese, si es válido, luego de dar clic en el botón "Agregar" deberá mostrarse en la casilla que corresponda. Caso contrario deberá mostrar el mensaje de error que ya se muestra ahora.

Luego deberá ir avanzando con este mismo comportamiento para las siguientes casillas.

Cuando estén completadas todas las casillas, muestra un botón "Completar" debajo de la fecha. Al dar clic en este botón, que deje de mostrar el sudoku y coloque un texto indicando "La fecha ingresada es: " seguido de la fecha que dio como resultado arriba.
```

**Qué intentaba lograr:** hacer más simple la interacción, evitando que el usuario tuviera que completar las nueve casillas vacías para ingresar un solo dígito.

**Qué cambió:** pasó a ser suficiente completar correctamente una casilla. También se agregó el botón para completar el proceso y mostrar la fecha obtenida.

---

## 3 — Validar y reiniciar

```
Tienes que validar la fecha final, si es una fecha inválida debes mostrar un mensaje de error y pedir que la ingrese de nuevo.

Agrega un botón "Reiniciar" arriba de la fecha y que al dar clic, limpie todas las casillas y deba iniciarse nuevamente.
```

**Qué intentaba lograr:** evitar que se aceptaran fechas inexistentes y permitir comenzar de nuevo en cualquier momento.

**Qué cambió:** se agregó la validación final de la fecha, un mensaje de error para fechas inválidas y el botón **Reiniciar**.

---

## Conversación completa

El trabajo se desarrolló en una sola conversación con Codex, manteniendo el mismo archivo HTML durante las tres iteraciones.
