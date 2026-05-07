# Frontend Rules

## DO
- Keep templates clear, accessible, and consistent with the current Django layout.
- Reuse partials and blocks instead of duplicating markup.
- Make form errors visible and actionable.
- Preserve mobile responsiveness and existing navigation patterns.

## DO NOT
- Do not move business decisions into templates.
- Do not hide validation errors.
- Do not add JavaScript complexity unless it solves a concrete UX need.

## Quality Gates
A frontend change is valid only if:
- The target template still renders with the context provided by the view.
- The UI remains readable on desktop and mobile.