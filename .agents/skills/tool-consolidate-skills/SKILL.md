---
name: tool-consolidate-skills
description: "Consolidate overlapping guidance across project skills and top-level Copilot instructions. Use when: copilot-instructions.md is getting bloated, multiple skills repeat the same rule, guidance belongs in the wrong file, or a long skill should be split into references, assets, or scripts."
argument-hint: "What guidance should be consolidated?"
---

# Consolidate Skills

## Purpose

Keep project guidance simple, discoverable, and maintainable by giving each rule one clear home. Use `copilot-instructions.md` for always-on repo rules and routing. Use skills for domain-specific guidance. Use skill subfiles for large supporting material.

## When to use this skill

- Reducing duplication across `.agents/skills/`.
- Trimming `copilot-instructions.md` without losing important rules.
- Moving guidance into the right owning skill.
- Splitting a large skill into smaller references, assets, or scripts.
- Reviewing whether a rule should be always-on or only loaded on demand.

## Procedure

1. Inventory the current guidance.
   - List the relevant rules in `copilot-instructions.md` and the affected skills.
   - Note duplicate, conflicting, or misplaced guidance.
2. Choose the right home for each rule.
   - Keep always-on project workflow, approval, and safety rules in `copilot-instructions.md`.
   - Move implementation guidance into the owning skill.
   - Move large examples, checklists, or templates into skill subfiles.
3. Consolidate to a single source of truth.
   - Remove duplicate wording instead of keeping multiple nearly identical copies.
   - Leave short routing summaries at the top level when the detailed rule now lives in a skill.
   - Update skill descriptions so the moved guidance stays discoverable.
4. Verify the result.
   - Check that each rule has one primary home.
   - Check that the top-level instructions are still short and durable.
   - Check that skill references use relative `./` paths.
   - Check that no moved guidance became harder to find.

## Decision Rules

- If a rule applies to most work in the repo, keep it in `copilot-instructions.md`.
- If a rule is specific to a domain like styling, Next.js, or code conventions, move it into that skill.
- If a skill is getting long, split detailed material into [reference files](./references/checklist.md) or other subfiles.
- If ownership is unclear, ask which file should be the source of truth before duplicating the rule.

## Completion Checks

- Each important rule exists in one primary location.
- `copilot-instructions.md` contains routing and durable repo rules, not domain detail.
- Skill descriptions still contain the trigger words needed for discovery.
- Supporting material is moved into subfiles when that makes the entry skill easier to scan.
