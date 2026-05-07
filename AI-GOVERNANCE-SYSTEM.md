# AI Governance System — Guía Completa

> Sistema estructurado de trabajo con IA basado en instrucciones globales,
> agentes especializados y specs de features. Adaptable a cualquier proyecto.

---

## Cómo funciona el sistema

El proyecto implementa una **arquitectura de gobernanza de IA** con tres capas que se encadenan:

```
.github/instructions/copilot.instructions.md   ← Reglas globales de comportamiento
agents/
  ├── {rol}/agent.md        ← Qué sabe y NO sabe hacer cada agente
  ├── {rol}/rules.md        ← Reglas estrictas del dominio
  ├── {rol}/templates.md    ← Ejemplos concretos de output esperado
  └── specs/
      └── *.spec.md         ← Contrato detallado de cada feature
```

### Capa 1 — `copilot.instructions.md` (reglas de orquestación)
Define el **comportamiento base** del AI antes de responder cualquier cosa:
- Siempre diagnosticar antes de solucionar
- Siempre verificar después de resolver
- Siempre preguntar antes de asumir
- Siempre ofrecer commit al terminar

### Capa 2 — Agentes especializados (rol + reglas + templates)
Cada carpeta en `/agents` define un **agente con identidad**: sabe qué le compete,
qué está fuera de su scope, y cómo debe producir output.

### Capa 3 — Specs (contratos de feature)
Archivos `.spec.md` que funcionan como **brief técnico completo** de una funcionalidad:
actores, casos de uso, modelo de datos, endpoints, validaciones, reglas de negocio,
seguridad, entregables y fases. El AI tiene contexto suficiente para implementar sin adivinar.

---

## ESTRUCTURA DE ARCHIVOS A CREAR

```
.github/
└── instructions/
    └── copilot.instructions.md    ← Reglas globales de comportamiento

agents/
├── architecture/
│   ├── agent.md        ← Scope del agente arquitectura
│   ├── rules.md        ← Reglas de arquitectura del proyecto
│   └── templates.md    ← Ejemplos de ADR, diagramas, decisiones
├── frontend/
│   ├── agent.md        ← Scope: UI, componentes, estado
│   ├── rules.md        ← Reglas: TypeScript estricto, capas, patrones
│   └── templates.md    ← Ejemplos de componentes, hooks, servicios
├── backend/
│   ├── agent.md        ← Scope: lógica de negocio, APIs, controllers
│   ├── rules.md        ← Reglas: Clean Architecture, validaciones
│   └── templates.md    ← Ejemplos de endpoints, servicios, repositorios
├── database/
│   ├── agent.md        ← Scope: modelado, índices, reglas de seguridad
│   ├── rules.md        ← Reglas: normalización, naming, permisos
│   └── templates.md    ← Ejemplos de schemas, queries, security rules
├── auth-security/
│   ├── agent.md        ← Scope: autenticación, autorización, tokens
│   ├── rules.md        ← Reglas: nunca exponer secrets, validar siempre
│   └── templates.md    ← Ejemplos de guards, middleware, reglas
├── testing/
│   ├── agent.md        ← Scope: unit, integration, e2e
│   ├── rules.md        ← Reglas: coverage mínimo, qué testear
│   └── templates.md    ← Ejemplos de tests por capa
├── devops/
│   ├── agent.md        ← Scope: CI/CD, deploy, infra
│   ├── rules.md        ← Reglas: environments, secrets, rollback
│   └── templates.md    ← Ejemplos de pipelines, configs
├── documentation/
│   ├── agent.md        ← Scope: README, API docs, ADR
│   ├── rules.md        ← Reglas: sin emojis, técnico, actualizado
│   └── templates.md    ← Ejemplos de estructura de docs
├── commits/
│   ├── agent.md        ← Scope: gestión de git, mensajes, staging
│   ├── rules.md        ← Reglas: Conventional Commits, atómicos
│   └── templates.md    ← Ejemplos de buenos/malos commits
└── specs/
    └── [feature-name].spec.md     ← Un archivo por feature (ver formato)
```

---

## CONTENIDO DE CADA ARCHIVO

### `.github/instructions/copilot.instructions.md`

```markdown
---
applyTo: '**'
---
Before answering any user request:

- [ ] If the request involves a problem, bug, or issue: ALWAYS perform an
      issue diagnosis first (location, root cause, symptoms, why it happened)
      before providing a solution.

- [ ] After resolving a bug: explain the solution applied so the user
      understands it and can prevent similar issues.

- [ ] After any code change (feature, fix, refactor): ALWAYS offer the user
      two options: (1) save changes with a commit following the commits agent
      rules, or (2) continue with another change.

- [ ] After fixing an issue: run a test or verification step to confirm
      the fix works.

- [ ] Always read the relevant agent files before acting within their domain.

- [ ] Always ask for clarification if the request is ambiguous.

- [ ] No unnecessary assumptions. If information is missing, ask first.

- [ ] Use agents as hierarchical roles — each agent owns its domain.

- [ ] Follow architecture and agent-specific rules strictly.
```

---

### `agents/{rol}/agent.md` — Patrón de contenido

Cada `agent.md` debe responder:
- **Responsible for:** lista de tecnologías/dominios que le pertenecen
- **Works exclusively in:** capa del sistema que gobierna
- **Never does:** restricciones duras de lo que no puede hacer
- **Interacts with:** cómo se comunica con otros agentes/capas

Ejemplo para Backend:

```markdown
# Backend Agent

Responsible for:
- Node.js / Express / [tu framework]
- Business logic and use cases
- Controllers and request handling
- API response formatting
- Input validation

Works exclusively in the business and application layer.

Never implements UI logic.
Never accesses the database directly — always through repositories.
Never exposes internal errors directly to the client.

Architecture: Controller → UseCase/Service → Repository
```

---

### `agents/{rol}/rules.md` — Patrón de contenido

Lista de DO y DO NOT concretos y verificables:

```markdown
# {Rol} Rules

## DO
- [Regla específica y verificable]
- [Regla específica y verificable]

## DO NOT
- [Prohibición clara]
- [Prohibición clara]

## Quality Gates
A change from this agent is valid only if:
- [Condición 1]
- [Condición 2]
```

---

### `agents/{rol}/templates.md` — Patrón de contenido

Mínimo 2-3 ejemplos completos y reales del output esperado de ese agente.
- Para commits: ejemplos de buenos y malos mensajes.
- Para frontend: ejemplo de componente bien estructurado.
- Para backend: ejemplo de controller + service + repository.

---

### `agents/specs/[feature-name].spec.md` — Formato de Spec

Este es el formato estándar para documentar una feature antes de implementarla:

```markdown
# SPEC: [Nombre de la Feature]

**Version:** 1.0
**Date:** YYYY-MM-DD
**Status:** Draft | In Development | Done
**Author:** [Team o persona responsable]

---

## Overview
Descripción de qué hace esta feature y por qué existe.

### Context
- Qué ya existe que sea relevante
- Qué depende de esto
- Qué falta construir

---

## Actors
1. **[Actor 1]** — rol y permisos
2. **[Actor 2]** — rol y permisos

---

## Use Cases

### UC-1: [Nombre del caso de uso]
**Actor:** [quién lo ejecuta]
**Precondition:** [estado necesario]
**Flow:**
1. Paso 1
2. Paso 2
3. ...
**Postcondition:** [estado resultante]

---

## Data Model

interface [EntityName] {
  // Campos existentes (no modificar)
  id: string

  // Campos nuevos
  newField: string
}

---

## API Endpoints

### 1. METHOD /api/[ruta]
**Auth:** Bearer Token / Public

**Request Body:**
{ "field": "value" }

**Response 200:**
{ "success": true, "data": {} }

**Response 4xx:**
{ "success": false, "error": "mensaje" }

---

## Business Rules

### BR-1: [Nombre de la regla]
Descripción exacta de la regla.

---

## Security

### Access control rules
[Pseudocódigo o código real de las reglas de acceso]

---

## Edge Cases & Validations

1. **[Campo/Situación]**
   - Condición mínima/máxima
   - Formato esperado
   - Comportamiento ante datos inválidos

---

## Deliverables

### Backend
- [ ] Archivo de rutas
- [ ] Controlador
- [ ] Servicio
- [ ] Repositorio
- [ ] Tests unitarios

### Frontend
- [ ] Componente/página
- [ ] Servicio de conexión con API
- [ ] Tests

---

## Implementation Plan

### Phase 1: [Nombre]
1. Paso 1
2. Paso 2

### Phase 2: [Nombre]
...

---

## Dependencies

### Depends on:
- [Sistema X] (ya existe / pendiente)

### Is a dependency of:
- [Sistema Y]

---

## Technical Notes
1. Nota importante #1
2. Nota importante #2
```

---

## CÓMO USAR EL SISTEMA EN EL DÍA A DÍA

### Flujo de trabajo estándar con el AI

**Para bugs:**
```
Tengo un problema: [descripción].
Archivo: [ruta]. Error: [mensaje].
```
El AI diagnostica primero, luego resuelve, luego verifica, luego ofrece commit.

**Para features:**
```
Implementa la feature descrita en agents/specs/[nombre].spec.md
usando el agente de [frontend|backend|database].
```
El AI lee la spec, sigue las reglas del agente correcto, produce el código.

**Para commits:**
```
Guarda los cambios con un commit.
```
El AI sigue el `agents/commits/rules.md` y `templates.md` para el mensaje.

**Para crear una nueva feature desde cero:**
```
Crea una spec en agents/specs/[nombre].spec.md para la feature:
[descripción en lenguaje natural de la feature]
```
El AI genera el `.spec.md` completo en el formato estándar antes de escribir código.

---

## PRINCIPIOS DEL SISTEMA

1. **Spec antes de código** — nunca implementar sin spec aprobada
2. **Diagnóstico antes de solución** — nunca resolver sin entender la causa raíz
3. **Agente correcto para cada tarea** — respetar la separación de dominios
4. **Commits atómicos y descriptivos** — el historial git es documentación
5. **Preguntar antes de asumir** — el AI no adivina, pregunta
6. **Verificar después de implementar** — siempre confirmar que funciona
7. **El usuario tiene control de cuándo commitear** — el AI no commitea solo

---

## ADAPTACIÓN AL STACK TECNOLÓGICO

Al crear los archivos `agent.md` y `rules.md`, reemplaza las tecnologías
genéricas con las tecnologías concretas de tu proyecto:

| Slot genérico  | Reemplazar con ejemplo concreto         |
|----------------|-----------------------------------------|
| Frontend fw    | React, Vue, Angular, Svelte, etc.       |
| Backend fw     | Express, Fastify, NestJS, Django, etc.  |
| Database       | Firestore, PostgreSQL, MongoDB, etc.    |
| Auth provider  | Firebase Auth, Auth0, Supabase, etc.    |
| Hosting/Infra  | Firebase, Vercel, AWS, Railway, etc.    |
| Test framework | Jest, Vitest, Pytest, etc.              |
| Commit style   | Conventional Commits / mApache / custom |

---

## PROMPT DE SETUP PARA UN PROYECTO NUEVO

Pegá este prompt al inicio de cualquier proyecto nuevo para activar el sistema:

```
Eres un asistente de desarrollo de software. Este proyecto utilizará un sistema
estructurado de trabajo con IA basado en tres capas:

1. Instrucciones globales en .github/instructions/copilot.instructions.md
2. Agentes especializados en agents/{rol}/agent.md + rules.md + templates.md
3. Specs de features en agents/specs/[nombre].spec.md

Reglas de comportamiento obligatorias:
- Antes de resolver un bug: diagnosticar causa raíz, síntomas y ubicación
- Después de cualquier cambio: ofrecer al usuario commitear o continuar
- Antes de asumir: preguntar si falta información
- Al actuar en un dominio: leer y respetar el agent.md y rules.md correspondiente
- Al implementar una feature: leer la spec completa antes de escribir código
- Al hacer un commit: seguir el formato de agents/commits/rules.md

Stack de este proyecto:
- Frontend: [tecnología]
- Backend: [tecnología]
- Base de datos: [tecnología]
- Auth: [tecnología]
- Hosting: [tecnología]

Arquitectura de capas:
[describir el patrón: ej. Controller → Service → Repository]

Comienza leyendo los archivos de agents/ si existen, o créalos si es un proyecto nuevo.
```
