---
name: preentrega-coffee-atlas
description: Audita Coffee Atlas V2 antes de entregar, comprobando alcance, seguridad, Git, tests, migraciones, aislamiento, navegador y documentación sin reparar automáticamente.
---

# Preentrega de Coffee Atlas V2

Realizá primero un diagnóstico de sólo lectura. No corrijas fallas, no modifiques
datos reales y no hagas commits hasta recibir autorización posterior.

## Procedimiento

1. Confirmá que el directorio es `tp-final` y revisá todos los `AGENTS.md`.
2. Revisá estado, diff, whitespace y staged; señalá archivos ajenos al alcance.
3. Confirmá que `docs/spec.md`, `docs/plan.md`, `docs/spec-v2.md` y
   `docs/plan-v2.md` no tengan cambios retroactivos.
4. Contrastá routers, modelos y frontend con `docs/spec-v2.md`; no apliques las
   restricciones de seis endpoints/tabla única de V1 al producto V2.
5. Auditá aislamiento, CSRF/Origin, cookies, hosts, encabezados, secretos, logs,
   SSRF, uploads y sesión fail-closed.
6. Auditá Place ID, TTL, contenido Google vivo, atribución y ubicación actual
   efímera. Confirmá que los tests no realizan red.
7. Ejecutá con caché temporal y modo offline:

   ```bash
   UV_CACHE_DIR=/private/tmp/coffee-atlas-uv-cache uv run --offline pytest -q
   UV_CACHE_DIR=/private/tmp/coffee-atlas-uv-cache uv run --offline python -m compileall backend
   ```

8. Confirmá que `.env`, bases, backups, uploads, caches y entornos estén
   ignorados y no versionados. No abras `.env` ni datos personales.
9. No ejecutes comandos sobre la base real sin autorización específica. Si
   corresponde, compará sólo huellas antes/después de pruebas.
10. Con servidor temporal y dobles, recorré `docs/browser-checklist-v2.md`:
    320/768/1440, teclado, consola, degradación, fallback y dos identidades.
11. Contrastá README, `docs/verification-v2.md`, Términos y Privacidad con la
    evidencia observada.

## Informe final

Separá el resultado en listo, fallas bloqueantes y mejoras no bloqueantes. Para
cada falla incluí evidencia, archivo/comando y criterio de resolución. Indicá
qué verificaciones reales quedaron fuera por falta de autorización. No repares
automáticamente.
