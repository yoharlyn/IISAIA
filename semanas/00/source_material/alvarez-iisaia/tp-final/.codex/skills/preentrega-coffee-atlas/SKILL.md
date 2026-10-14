---
name: preentrega-coffee-atlas
description: Audita Coffee Atlas antes de entregar, comprobando alcance, Git, tests, API, persistencia, navegador, documentación y evidencia sin reparar automáticamente.
---

# Preentrega de Coffee Atlas

Realizá primero un diagnóstico de solo lectura y reportá resultados concretos.
No modifiques archivos, no borres la base, no hagas commits y no corrijas fallas
hasta recibir una autorización posterior.

## Procedimiento

1. Confirmá que el directorio actual es el `tp-final` del repositorio del alumno
   y no el repositorio de material del profesor.
2. Revisá `git status --short`, `git diff --stat`, `git diff --check` y la lista
   de archivos cambiados. Señalá cualquier cambio externo a `tp-final`.
3. Verificá que `docs/plan.md` siga siendo el plan aprobado y que las diferencias
   reales estén explicadas en el README.
4. Confirmá que existen exactamente los seis endpoints previstos y que no se
   amplió el alcance.
5. Ejecutá `uv run pytest -q` y `uv run python -m compileall backend`. Informá
   cantidad de tests, fallas y warnings; no los ocultes.
6. Comprobá que `data/coffee_atlas.db`, caches y entornos estén ignorados y no
   versionados.
7. Con la aplicación disponible, recorré `docs/browser-checklist.md` mediante
   Playwright si está disponible. Si no lo está, indicá claramente qué pasos
   deben verificarse de forma manual.
8. Contrastá `docs/verification.md` y el README con la evidencia observada.

## Informe final

Separá el resultado en: listo, fallas bloqueantes y mejoras no bloqueantes.
Para cada falla incluí evidencia, archivo o comando afectado y criterio para
considerarla resuelta. Cerrá con una lista corta y ordenada de acciones previas
a la entrega, sin ejecutarlas.

