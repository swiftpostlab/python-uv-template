---
name: ai-safety
description: "AI policy, protected file access, and exclusion sync. Use when: modifying .ai-policy.json, updating the sync script, or reviewing AI safety configuration."
---

# AI Safety

## Purpose

Document how AI agents are prevented from accessing sensitive files, how noisy/generated files are excluded from context, and how the policy is synced across agent-specific configurations.

## Values

- Prefer simplicity over cleverness.
- Prefer maintainability over short-term convenience.
- Keep policy synchronization deterministic and easy to audit.

## When to use this skill

- Adding or modifying protected or excluded file patterns.
- Updating the sync script.
- Reviewing AI safety configuration.

## Architecture Overview

```
.ai-policy.json                     ← Source of truth
    │
    ├── scripts/sync_ai_policy.py   ← Sync script
    │       │
    │       ├── .aiexclude                 → generated for Gemini/native exclusion
    │       ├── .claude/settings.json      → permissions.deny with protected Read() patterns
    │       └── .vscode/settings.json      → protected file associations + command/edit guardrails
    │
    └── .github/copilot-instructions.md    ← Behavioral directive (all agents via CLAUDE.md/GEMINI.md)
```

## Protected vs Excluded

- `protectedFiles`: security-sensitive files that must not be read or modified.
- `excludedFiles`: low-signal generated output or noise that should usually stay out of agent context, but are not secrets by default.

## How Each Agent Is Restricted

| Agent | File-Level Restriction | Behavioral Instruction |
|-------|----------------------|----------------------|
| **Gemini** | Generated `.aiexclude` (protected + excluded patterns) | GEMINI.md → copilot-instructions.md |
| **Claude Code** | `.claude/settings.json` `permissions.deny` with protected `Read()` patterns | CLAUDE.md → copilot-instructions.md |
| **GitHub Copilot** | `.vscode/settings.json` protected file deterrent plus command/edit guardrails | `.github/copilot-instructions.md` security directive |

### Copilot Limitation

The `.vscode/settings.json` approach maps protected patterns to a `copilot-restricted-file` language ID and disables Copilot for that ID. This is a **best-effort workaround** — `copilot-restricted-file` is not a real language ID. The behavioral directive in `copilot-instructions.md` is still the primary enforcement.

## Updating Policy

1. Edit `.ai-policy.json`.
2. Put sensitive patterns in `protectedFiles`.
3. Put noisy/generated output in `excludedFiles`.
4. Update top-level `terminalAutoApprove` and `editAutoApprove` rules when needed.
5. Run `uv run sync-ai-policy` to propagate changes.
6. Commit all generated files (`.aiexclude`, `.claude/settings.json`, `.vscode/settings.json`).

If you want to promote approvals that VS Code added interactively after the user greenlit a command, run `uv run sync-ai-policy-import-vscode`. That imports the current VS Code terminal/edit approvals into `.ai-policy.json` first, then performs the normal sync.

## Sync Script

**Location:** `scripts/sync_ai_policy.py`
**Run (recommended):** `uv run sync-ai-policy`
**Import VS Code approvals:** `uv run sync-ai-policy-import-vscode` (merges current VS Code approvals into `.ai-policy.json` then syncs)
**Requires:** Python >= 3.14

The script reads `.ai-policy.json` and writes:
- `.aiexclude` — protected + excluded patterns for Gemini/native exclusion
- `.claude/settings.json` — `permissions.deny` array with `Read(<pattern>)` entries for protected files
- `.vscode/settings.json` — protected `files.associations`, `github.copilot.enable`, and generated terminal/edit rules

The command/edit policy is kept at the top level of `.ai-policy.json`. The script does not carry built-in approval defaults. It writes the managed approval sections from the policy so the generated files stay aligned with the source of truth instead of accumulating stale template-era rules.

When syncing `.claude/settings.json` and `.vscode/settings.json`, replace the policy-managed sections deterministically instead of appending to them. Removing an item from `.ai-policy.json` must remove the generated output on the next sync as well, while unrelated settings remain preserved where the script can distinguish them.

Keep this tool as a standalone repository script under `scripts/` unless the user explicitly asks to move it.

This repository intentionally keeps the implementation in `scripts/` while exposing the supported command through `[project.scripts]`.

Use the `--import-vscode` flag (also exposed via the `sync-ai-policy-import-vscode` entrypoint) to pull the current VS Code approval maps into `.ai-policy.json` first.
