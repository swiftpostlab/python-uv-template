---
name: skills-meta
description: "Suggestions on creating new and apt skills. Use when: designing new skills, updating existing skills, establishing skill standards, or evaluating skill quality."
---

# Skills

Use  <https://agentskills.io/home> and <https://github.com/anthropics/skills> as reference.
Ensure that the skills can be used across different providers and models
like (but not limited to) Copilot, OpenAI, Antropic, Gemini AI, Ollama.

## General

- Keep skills modular and focused on a single responsibility (e.g., one for coding conventions, one for deployment, one for data schema).
- Use a clear versioning system (e.g., SemVer) to track changes in the skill's logic.
- Include a "When to use this skill" section to help the AI determine the relevance of the instructions.
- Provide concrete examples of file structures or code snippets to minimize ambiguity.

## Communication Guidelines

- Provide direct, unfiltered feedback. The user is an adult and prefers the truth now over complaints later.
- Do not sugarcoat technical debt or architectural flaws.
- If a request is suboptimal, explain why immediately and suggest the correct path.

## Cross-platform Compatibility

Ensure that the instructions are applicable regardless of the AI provider or model, avoiding any provider-specific features or assumptions. Check that the instructions in the main md of each platform are consistent with each other and with the skills, so that the AI can rely on them regardless of the platform it is running on.

### Core instructions to include in all platforms' main md files:

 - .github\copilot-instructions.md
 - GEMINI.md

The content of these files should be consistent with each other and with the skills, so that the AI can rely on them regardless of the platform it is running on.

## Examples of Skill Setups

### 1. Documentation Skill (`docs-convention`)

Focuses on how the AI should document the code, ensuring consistency in docstrings and README files.

```markdown
---
name: docs-convention
description: "Rules for Python docstrings and project documentation. Use when: writing documentation, authoring docstrings, updating README files."
version: 0.1.0
---
# Documentation Rules
- Use Google-style docstrings for all public functions and classes.
- Every feature folder must contain a `README.md` explaining its purpose.
- Update the root `CHANGELOG.md` whenever a new feature is added.
```

### 2. API Integration Skill (`api-integration`)

Provides patterns for handling external API calls, error handling, and rate limiting.

```markdown
---
name: api-integration
description: "Standard patterns for external API consumers. Use when: implementing API calls, handling errors, managing rate limiting."
version: 0.1.0
---
# API Patterns
- Use `httpx` for asynchronous requests.
- Implement exponential backoff for 429 and 5xx status codes.
- Always define response schemas using Pydantic models in `models/`.
```

### 3. Database Migration Skill (`db-migrations`)

Specific instructions for managing database schemas and migration scripts.

```markdown
---
name: db-migrations
description: "Workflow for SQLAlchemy and Alembic migrations. Use when: creating database migrations, modifying schema, managing database changes."
version: 0.1.0
---
# Migration Workflow
- New tables must include `created_at` and `updated_at` timestamps.
- Migration scripts must be generated using `poetry run alembic revision --autogenerate`.
- Always provide a `downgrade` logic in the migration script.
```
