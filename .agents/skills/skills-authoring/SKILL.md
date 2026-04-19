---
name: skills-authoring
description: "Guidelines for creating and maintaining project skills. Use when: designing new skills, updating existing skills, establishing skill standards, evaluating skill quality, organizing skill subfiles, or adapting copied skill content to the repo's actual stack."
---

# Skills Authoring

## Purpose

Ensure project skills are focused, discoverable, simple to follow, and maintainable across different AI providers and models.

## When to use this skill

- Creating a new skill file.
- Reviewing or updating an existing skill.
- Evaluating whether a skill is well-structured.
- Adapting a copied skill so it matches this repository instead of preserving stale source-project details.

## References

Use <https://agentskills.io/home> and <https://github.com/anthropics/skills> as reference for best practices.

Use `./references/checklist.md` when reviewing or refactoring a skill, and `./references/template.md` when creating a new one.

## Values

- Prefer simplicity over cleverness.
- Prefer maintainability over short-term convenience.
- Keep skill guidance easy to find and audit.

## Skill File Rules

- **Location:** In this repo, project skills live at `.agents/skills/<skill-name>/SKILL.md`.
- **Folder structure:** A skill folder may include supporting subfiles when they keep the main skill focused.

```text
.agents/skills/<skill-name>/
├── SKILL.md
├── references/
├── scripts/
└── assets/
```

- **Supporting files are allowed:** Put long checklists, detailed examples, templates, or helper scripts in subfolders instead of cramming everything into `SKILL.md`.
- **Relative references only:** Link skill resources from `SKILL.md` with `./references/...`, `./scripts/...`, or `./assets/...` paths.
- **Keep loading progressive:** Keep `SKILL.md` concise and move large supporting material into subfiles. Prefer one-level-deep references from `SKILL.md`.
- **One responsibility per skill.** A skill about code conventions should not also cover deployment.
- **Frontmatter required:** Every skill must have `name` and `description` in YAML frontmatter.
- **Name must match folder:** The `name` field must match the skill folder name.
- **"When to use" section:** Include a clear section so the AI can determine relevance.
- **Concrete examples:** Provide code snippets or file structures to minimize ambiguity.
- **Provider-agnostic:** No provider-specific features or assumptions. Skills must work with Copilot, Claude, Gemini, and others.
- **Adapt to the real repo:** When a skill is copied or derived from another project, update its commands, libraries, file names, folder layout, and examples to match this repository before keeping it.
- **Do not preserve stale stack details:** Remove or replace inherited references to the wrong package manager, framework, language conventions, file extensions, or UI library when they do not match the current repo.
- **Name repo-specific skills explicitly:** If a skill depends on repo-only packages, conventions, or wrappers that would not transfer cleanly to another project, prefix or name it in a repo-specific way. Keep transferable guidance under generic names like `code-conventions`, `project-structure-setup`, or `skills-authoring`.
- **Make values explicit:** When a skill depends on values like simplicity, clarity, or maintainability, state them directly in the purpose or rules instead of leaving them implicit.
- **Prefer modern defaults:** When a skill gives coding guidance, prefer modern, intention-revealing language and platform APIs over older sentinel-style patterns when both are supported by the project's runtime targets.
- **Prefer operational labels:** When naming workflow steps or guidance sections, prefer labels that describe the actual review/update action. Favor concrete labels like `Reflect` or `Capture Lessons` over vaguer labels like `Learn` when the step includes reviewing outcomes, correcting guidance, and updating the source of truth.

## Cross-Platform Parity

Keep instructions consistent across all platform-specific files:

| File | Platform |
|------|----------|
| `.github/copilot-instructions.md` | GitHub Copilot |
| `GEMINI.md` | Google Gemini |
| `CLAUDE.md` | Anthropic Claude |

The Copilot instructions file is the source of truth.

Default pattern for this repo and most repos:

- Put the real guidance in `.github/copilot-instructions.md`.
- Make `GEMINI.md` and `CLAUDE.md` thin reference files that tell the agent to read the Copilot instructions first.
- Do not duplicate the same workflow, commands, or policy text across all three files when a reference is enough.

Cross-platform parity means the effective guidance should match across providers, not that every file must contain the same amount of text.

Only add provider-specific text in `GEMINI.md` or `CLAUDE.md` when there is a real platform-specific need, such as:

- a required bootstrap instruction that must appear in that provider's entry file,
- a provider-specific limitation or capability that changes how the repo must be operated,
- or a provider-specific routing note that cannot live solely in the shared Copilot instructions.

When that happens:

- keep the provider-specific file minimal,
- state only the platform-specific exception,
- and route back to `.github/copilot-instructions.md` for the actual repo guidance.

If there is no real provider-specific behavior, nothing else needs to be done beyond the reference stub.

## Communication Guidelines

- Provide direct, unfiltered feedback. The user prefers honesty over comfort.
- Do not sugarcoat technical debt or architectural flaws.
- If a request is suboptimal, explain why immediately and suggest the correct path.

## Reference Files

- Use `./references/checklist.md` to review whether a skill is focused, discoverable, and adapted to the real repo.
- Use `./references/template.md` as the default scaffold for new skills.
