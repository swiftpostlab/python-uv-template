---
name: ai-safety
description: "AI policy, protected file access, and exclusion sync. Use when: modifying .ai-policy.json, updating the sync script, or reviewing AI safety configuration."
---

# AI Safety

---
name: ai-safety
description: "AI policy, protected file access, and exclusion sync. Use when: modifying .ai-policy.json, updating the sync script, or reviewing AI safety configuration."
---

# AI Safety

## Purpose

Document how AI agents are prevented from accessing sensitive files, how noisy/generated files are excluded from context, and how the policy is synced across agent-specific configurations.

## When to use this skill

- Adding or modifying protected or excluded file patterns.
- Updating the sync script.
- Reviewing AI safety configuration.

## Architecture Overview

```
.ai-policy.json                     ← Source of truth
    │
    ├── scripts/sync-ai-ignores.mts  ← Sync script (runs on `yarn install`)
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
5. Run `yarn sync:ai` to propagate changes.
6. Commit all generated files (`.aiexclude`, `.claude/settings.json`, `.vscode/settings.json`).

If you want to promote approvals that VS Code added interactively after the user greenlit a command, run `yarn sync:ai:import`. That imports the current VS Code terminal/edit approvals into `.ai-policy.json` first, then performs the normal sync.

## Sync Script

**Location:** `scripts/sync-ai-ignores.mts`
**Run:** `yarn sync:ai` or `yarn sync:ai:import` (also runs automatically on `yarn install` via `prepare` hook)
**Requires:** Node >= 22.6 (native type stripping)

The script reads `.ai-policy.json` and writes:
- `.aiexclude` — protected + excluded patterns for Gemini/native exclusion
- `.claude/settings.json` — `permissions.deny` array with `Read(<pattern>)` entries for protected files
- `.vscode/settings.json` — protected `files.associations`, `github.copilot.enable`, and generated terminal/edit rules

The command/edit policy is kept at the top level of `.ai-policy.json` even though it currently syncs only into `.vscode/settings.json`. That keeps the source model agent-agnostic and makes it easier to map the same intent into Gemini or Claude-specific settings if those tools expose compatible controls later.

When syncing `.claude/settings.json` and `.vscode/settings.json`, the script merges policy-managed entries into the existing files instead of replacing the full permission maps. This preserves command approvals that VS Code may add interactively when the user greenlights a command.

`yarn sync:ai:import` is the explicit reverse flow. It imports the current `.vscode/settings.json` terminal/edit approval maps into `.ai-policy.json`, then runs the normal forward sync so the shared policy catches up to the locally approved commands.
