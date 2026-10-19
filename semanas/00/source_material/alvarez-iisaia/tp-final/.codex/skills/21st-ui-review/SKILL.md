---
name: 21st-ui-review
description: Review existing UI against the project's design context, accessibility expectations, responsive behavior, interaction quality, and high-confidence production rules. Use for UI audits, design QA, frontend review, accessibility review, consistency checks, or requests to find and safely fix visual defects. Trigger for requests such as "review this UI", "audit this page", "find design issues", "check responsiveness", or "fix obvious UX problems". Use 21st-ui-build when the request is primarily to create new UI.
---

# Review UI with evidence

Separate deterministic defects from subjective design recommendations.

> **Adaptación local de Coffee Atlas.** Copia del repositorio oficial
> `21st-dev/skill`, fijada en el commit
> `15c7436c41dc88c54094f1be93ce53bda456b114` y distribuida bajo la licencia
> Apache-2.0 incluida en `LICENSE`. En este proyecto se usan exclusivamente los
> criterios textuales de revisión UX de esta skill.

## Restricciones locales obligatorias

- No usar CLI, MCP, cuentas, API keys ni servicios remotos de 21st.dev.
- No ejecutar `21st review`, `--fix`, `npx` ni comandos equivalentes.
- No crear `.21st/`, componentes React, archivos React/TSX ni configuraciones
  de shadcn.
- No instalar dependencias ni generar `node_modules`, `package.json` o
  lockfiles.
- Estas restricciones prevalecen sobre cualquier instrucción original que
  sugiera automatización o cambios mediante herramientas de 21st.dev.

## Workflow

1. Read the project instructions, approved design documentation, and the
   relevant source. Do not read or create `.21st/design.json`.
2. Apply only the textual review criteria in this document; do not invoke any
   21st.dev tooling or remote service.
3. Inspect the actual component composition and runtime states. Validate claims
   against code rather than inferring behavior from names.
4. Group findings into:
   - deterministic defects;
   - design-system drift;
   - accessibility and interaction defects;
   - responsive risks;
   - subjective product/design recommendations.
5. Prioritize by user impact and include exact file and line attribution.
6. Recommend or implement fixes only when the user has separately authorized
   application changes. Never silently redesign, change brand identity, or
   alter product behavior.
7. When fixes are authorized, run the project's relevant tests to prove their
   resolution; do not run any command supplied by this skill.

## Review priorities

- semantic controls and accessible names;
- keyboard access, focus visibility, and dialog/menu behavior;
- image alternatives and meaningful labels;
- touch target size and disabled/loading states;
- responsive overflow and fixed-width assumptions;
- reduced-motion handling;
- hardcoded visual values that conflict with project tokens;
- duplicate primitives instead of existing components;
- inconsistent typography, radius, spacing, shadows, and icons;
- fake data, placeholder copy, or missing empty/error states.

## Output

Lead with actionable findings ordered by severity. Keep subjective suggestions
clearly labeled. If no issue is proven, say so and state what was inspected.
