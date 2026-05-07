# Backend Rules

## DO
- Validate inputs close to the view or form boundary.
- Keep business rules in reusable helpers or model methods when they are shared.
- Use Django ORM and transactions for data changes that must stay consistent.
- Preserve current permission and session behavior unless the task explicitly changes it.

## DO NOT
- Do not mix presentation concerns into backend logic.
- Do not bypass Django validation to silence errors.
- Do not change production paths or hosts without verifying the PythonAnywhere deployment impact.
- Do not add new package dependencies unless the code really needs them.

## Quality Gates
A backend change is valid only if:
- The affected path still works with the current Django settings.
- The smallest relevant verification step passes or is documented.