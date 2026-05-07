# Database Rules

## DO
- Prefer explicit constraints and clear relation names.
- Protect production data with careful migration planning.
- Keep foreign key behavior intentional and documented.

## DO NOT
- Do not remove uniqueness or validation rules casually.
- Do not create migrations that depend on manual data fixes unless they are documented.
- Do not change the database engine without confirming deployment support.

## Quality Gates
A database change is valid only if:
- The migration is reversible or the risk is explicitly documented.
- Existing records are not silently invalidated.