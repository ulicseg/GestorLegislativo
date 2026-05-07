# Auth Security Rules

## DO
- Enforce access checks at the view or decorator boundary.
- Keep session and CSRF settings explicit and environment aware.
- Review role-based logic when model relationships change.

## DO NOT
- Do not hardcode secrets or tokens.
- Do not rely on client-side checks for authorization.
- Do not widen permissions without a documented reason.

## Quality Gates
A security change is valid only if:
- The access rule is testable or manually verifiable.
- No sensitive values are exposed in the change.