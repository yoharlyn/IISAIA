# TP 1 — Ingreso de fecha de nacimiento a través de sudokus.

Una página web para ingresar una fecha de nacimiento de una manera poco convencional: cada dígito distinto de cero debe obtenerse completando una casilla válida de un sudoku.

## Cómo se ejecuta

Abrir `index.html` en cualquier navegador. Es un único archivo con HTML, CSS y JavaScript, sin frameworks.

## Qué me propuse construir

Una interfaz simple que transforme el ingreso de una fecha en una serie de sudokus. Antes de cada sudoku se pregunta si el dígito es cero. Si no lo es, el usuario debe ingresar un número válido respetando las reglas del tablero.

## Decisiones que tomé yo

- Mostrar un sudoku distinto para cada dígito.
- Dejar una casilla vacía por cada número del 1 al 9, para que el usuario pueda elegir el dígito que necesita.
- Validar cada respuesta antes de agregarla a la fecha.
- Validar la fecha completa y permitir reiniciar el proceso en cualquier momento.

## Qué salió mal y cómo lo corregí

La primera versión exigía completar todas las casillas vacías del sudoku. Por eso, le pedí que simplificara el funcionamiento para que alcanzara con resolver una sola casilla correspondiente al dígito que necesitara ingresar, respetando las reglas del sudoku. Posteriormente, le pedí que agregara la validación final de la fecha y un botón para reiniciar el formulario.

El desarrollo se realizó mediante 3 iteraciones en una conversación con Codex.

## Prompts

El registro completo está en [prompts.md](prompts.md).
