---
applyTo: '**'
---
Before answering any request in this repository:

- Diagnose first when the request involves a bug, regression, or unexpected behavior. State the local cause, the affected surface, and the cheapest verification before proposing a fix.
- Read the relevant agent files before acting in that domain.
- Ask for clarification if the request is ambiguous or missing key constraints.
- After any code change, explain what changed and offer the user two paths: commit the changes or continue with another task.
- After any fix, run or propose a narrow verification step that can confirm the behavior.
- Do not assume new infrastructure, dependencies, or production settings without checking the existing Django project structure.
- Preserve the current deployment context for PythonAnywhere unless the user explicitly asks to change it.
- Prefer the smallest safe change that solves the stated problem.

Project context:

- Stack: Django 5.1 server-rendered app with templates, Django auth, SQLite for local development, CKEditor, ReportLab, and PythonAnywhere deployment.
- Main app areas: apps/proyectos, apps/usuario, apps/administrador.
- Treat the database, auth, templates, and deployment settings as production-sensitive.