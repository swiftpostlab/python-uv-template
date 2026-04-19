# Skill Authoring Checklist

Use this checklist when creating, reviewing, or refactoring a skill.

- Does the skill have one clear responsibility?
- Does the YAML frontmatter include `name` and `description`?
- Does the `name` field match the folder name?
- Does the skill include a clear `When to use` section?
- Does the guidance use this repo's actual commands, file paths, packages, and conventions?
- Were stale references from another project removed instead of preserved?
- If the skill is repo-specific, is that made explicit in the name or wording?
- Does `SKILL.md` stay concise, with long checklists, templates, or examples moved into `references/`, `assets/`, or `scripts/`?
- Are all links to supporting files relative `./references/...`, `./assets/...`, or `./scripts/...` paths?
- Does the skill avoid provider-specific assumptions unless a real platform-specific exception is required?
- If provider files are mentioned, does the skill preserve the reference-first pattern where `.github/copilot-instructions.md` is the source of truth and `GEMINI.md` / `CLAUDE.md` are thin stubs by default?
- Are workflow labels concrete and operational instead of vague?

Typical fixes:

- Move large templates out of `SKILL.md` and into `references/`.
- Replace inherited package-manager or framework examples with this repo's real stack.
- Split mixed guidance into separate skills when one file is trying to cover multiple domains.
