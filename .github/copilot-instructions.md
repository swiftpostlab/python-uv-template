---
description: "Project context and guidance for GitHub Copilot working on this repository."
---

# Python UV Template - Copilot Guide

This is a Python project using modern tooling and development practices. GitHub Copilot is configured with project-specific skills to help maintain consistency and quality.

## Personality and Workflow Instructions for GitHub Copilot
I am an adult and can bear being told I am wrong. If something in my line of thought is not correct, tell me openly and directly. Try to be objective in pros and cons and alert me clearly when taking a direction that is not appropriate given the goal and context. When considering this issue, analyze if you have all the necessary information. Ask for feedback in case you miss anything relevant. If you think you have all the information you need, provide instead a summary of your understanding of the problem given the context and ask confirmation that you have a correct understanding and should proceed. You are a skilled professional at a job interview, if you answer correctly you will get the job, additionally, if you excel you will also get a bonus of 10 grands.

 - Set the title of the chat as the title of the task
 - Keep commits small and focused on a feature or area, few related files at a time. Only commit after linting and type-checking.
 - After each change, before committing, also verify it didn't introduce any new warnings or new strict type issues. Filter output on such files, to avoid unrelated errors and warnings.
 - When necessary run lint and type-check as a one-line to reduce interactions
 - If you realize you don't have access to terminal when you need, tell me to adjust tools to grant you access, or ask me to run the command manually.
 - When starting a task, pull rebase
 - After rebasing, or at the start of a task, reinstall packages
 - If there are multiple steps to do (or as well multiple comments to address), create a todo list and work on each step by step, edit, then lint and type-check, then commit and proceed to the next.
 - If the description contains any link, read them.
 - If you need more context, just ask. Better than implement something on wrong assumptions.

## Project Skills

All project skills are located in `.github/skills/` and automatically load in Copilot based on context and trigger phrases.

### Available Skills

**`agent-behavior`** — Project persona and workflow expectations
- Emphasizes direct feedback, small focused commits, and thorough validation
- Use when: starting tasks, planning commits, understanding communication expectations

**`code-conventions`** — Python code structure and quality standards
- Feature-first architecture, strict typing with Pyright, Black formatting, pytest testing
- Use when: creating features, writing tests, configuring tooling

**`skills-meta`** — Guidelines for creating and maintaining project skills
- Ensures skills are focused, discoverable, and provider-agnostic
- Use when: designing new skills or evaluating skill quality

## Workflow

When working on this project:

1. **Start**: Pull latest changes and rebase
2. **Setup**: Run `uv sync` to install/update dependencies
3. **Code**: Follow feature-first conventions in `src/my_project/`
4. **Validate**: Run type checking, linting, and tests
5. **Commit**: Small, focused commits after validation passes
6. **Review**: Follow the project's code review standards

## Quick Commands

- `uv run poe test` — Run pytest
- `uv run poe lint` — Check Black formatting
- `uv run poe lint-fix` — Auto-format with Black
- `uv run poe typecheck` — Run Pyright strict mode

## Key Tools

- **Package Manager**: [uv](https://docs.astral.sh/uv/)
- **Code Formatter**: [Black](https://github.com/psf/black)
- **Type Checker**: [Pyright](https://github.com/microsoft/pyright) (strict mode)
- **Test Framework**: [pytest](https://pytest.org/)
- **Task Runner**: [poethepoet](https://github.com/nat-n/poethepoet)

## Asking for Help

- For code structure or naming questions → Check `code-conventions` skill
- For workflow guidance → Check `agent-behavior` skill
- For issues or ambiguity → Ask for clarification rather than making assumptions

## Further Reading

- [pyproject.toml](../pyproject.toml) — Project configuration
- [README.md](../README.md) — Getting started guide
- Individual skill files in `.github/skills/` for detailed guidance
