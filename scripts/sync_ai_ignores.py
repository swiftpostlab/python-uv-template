"""
sync_ai_ignores.py

Python port of the repository's AI policy sync script.

Reads `.ai-policy.json` (single source of truth) and syncs to:
- `.aiexclude` (Gemini/native exclusion)
- `.claude/settings.json` (permissions.deny)
- `.vscode/settings.json` (Copilot + terminal/edit approvals)

Usage:
    python scripts/sync_ai_ignores.py [--import-vscode]

When invoked with `--import-vscode` the script will import the current
VS Code terminal/edit approvals into `.ai-policy.json` and write the file
back before performing the normal forward sync.

This module follows project `code-conventions` (typed, explicit, small functions).
"""
from __future__ import annotations

from argparse import ArgumentParser
from json import JSONDecodeError
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    import json5  # type: ignore
except Exception:
    json5 = None

ROOT = Path(__file__).resolve().parent.parent
AI_POLICY = ROOT / ".ai-policy.json"
AI_EXCLUDE = ROOT / ".aiexclude"
VSCODE_SETTINGS = ROOT / ".vscode" / "settings.json"
CLAUDE_SETTINGS = ROOT / ".claude" / "settings.json"

TerminalApprovalRule = Dict[str, Union[bool, Any]]
TerminalApprovalSetting = Union[bool, TerminalApprovalRule]

AiPolicy = Dict[str, Any]
VscodeSettings = Dict[str, Any]


def read_json_file(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback

    text = path.read_text(encoding="utf-8")
    # Prefer json5 if available (handles comments, trailing commas, single quotes)
    if json5 is not None:
        try:
            return json5.loads(text)
        except Exception:
            # fall through to fallback parsing
            pass

    try:
        return json.loads(text)
    except JSONDecodeError:
        # Attempt JSONC parsing: strip comments and trailing commas
        cleaned = _strip_jsonc(text)
        try:
            return json.loads(cleaned)
        except JSONDecodeError:
            raise


def _strip_jsonc(text: str) -> str:
    """Remove JavaScript-style comments (// and /* */) and trailing commas from JSONC input.

    This is a conservative parser that preserves string contents and only removes
    comment tokens that are outside of string literals.
    """
    def remove_comments(s: str) -> str:
        out: List[str] = []
        i = 0
        length = len(s)
        in_str = False
        str_char = ""
        while i < length:
            ch = s[i]
            # Handle string literals (preserve escapes)
            if in_str:
                out.append(ch)
                if ch == "\\":
                    if i + 1 < length:
                        out.append(s[i + 1])
                        i += 2
                        continue
                elif ch == str_char:
                    in_str = False
                i += 1
                continue

            # Not in string: detect comment starts or string starts
            if ch == '"' or ch == "'":
                in_str = True
                str_char = ch
                out.append(ch)
                i += 1
                continue

            # Line comment
            if ch == '/' and i + 1 < length and s[i + 1] == '/':
                i += 2
                while i < length and s[i] != '\n':
                    i += 1
                continue

            # Block comment
            if ch == '/' and i + 1 < length and s[i + 1] == '*':
                i += 2
                while i + 1 < length and not (s[i] == '*' and s[i + 1] == '/'):
                    i += 1
                i += 2 if i + 1 < length else 1
                continue

            out.append(ch)
            i += 1

        return ''.join(out)

    no_comments = remove_comments(text)
    # Remove trailing commas before } or ] using a regex lookahead
    no_trailing = re.sub(r",\s*(?=[}\]])", "", no_comments)
    return no_trailing


def write_json_file(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")


def write_text_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


T = Any


def merge_record(existing: Optional[Dict[str, T]], managed: Dict[str, T]) -> Dict[str, T]:
    merged: Dict[str, T] = dict(existing or {})
    merged.update(managed)
    return merged


def merge_unique_strings(existing: Optional[List[str]], managed: List[str]) -> List[str]:
    out: List[str] = list(dict.fromkeys((existing or []) + managed))
    return out


def build_ai_exclude_content(policy: AiPolicy) -> str:
    lines: List[str] = [
        "# ============================================================================== ",
        "# AI EXCLUSION FILE",
        "# Generated from .ai-policy.json",
        "# Protected files are sensitive; excluded files are mostly noise or generated output.",
        "# ==============================================================================",
        "",
        "# --- 1. Protected files ---",
    ]

    lines.extend(policy.get("protectedFiles", []))
    lines.append("")
    lines.append("# --- 2. Excluded noise / generated output ---")
    lines.extend(policy.get("excludedFiles", []))
    lines.append("")
    return "\n".join(lines)


def import_policy_from_vscode(policy: AiPolicy) -> AiPolicy:
    vscode: VscodeSettings = read_json_file(VSCODE_SETTINGS, {})

    term = merge_record(policy.get("terminalAutoApprove", {}), vscode.get("chat.tools.terminal.autoApprove", {}))
    edits = merge_record(policy.get("editAutoApprove", {}), vscode.get("chat.tools.edits.autoApprove", {}))

    new_policy = dict(policy)
    new_policy["terminalAutoApprove"] = term
    new_policy["editAutoApprove"] = edits
    return new_policy


def main() -> int:
    parser = ArgumentParser(description="Sync .ai-policy.json into agent-specific configuration files.")
    parser.add_argument("--import-vscode", action="store_true", help="Import VS Code approvals into .ai-policy.json first")
    args = parser.parse_args()

    if not AI_POLICY.exists():
        print("No .ai-policy.json found. Nothing to sync.")
        return 0

    policy: AiPolicy = read_json_file(AI_POLICY, {
        "protectedFiles": [],
        "excludedFiles": [],
        "terminalAutoApprove": {},
        "editAutoApprove": {},
    })

    effective = import_policy_from_vscode(policy) if args.import_vscode else policy

    if args.import_vscode:
        write_json_file(AI_POLICY, effective)
        print("Imported: VS Code approvals into .ai-policy.json")

    if not effective.get("protectedFiles") and not effective.get("excludedFiles"):
        print(".ai-policy.json has no file patterns. Nothing to sync.")
        return 0

    write_text_file(AI_EXCLUDE, build_ai_exclude_content(effective))
    print(f"Loaded {len(effective.get('protectedFiles', []))} protected patterns and {len(effective.get('excludedFiles', []))} excluded patterns")
    print("Synced: Gemini (.aiexclude)")

    # Claude
    claude = read_json_file(CLAUDE_SETTINGS, {})
    perms = claude.get("permissions") if isinstance(claude.get("permissions"), dict) else {}
    existing_deny = perms.get("deny") if isinstance(perms.get("deny"), list) else []
    new_deny = merge_unique_strings(existing_deny, [f"Read({p})" for p in effective.get("protectedFiles", [])])
    perms["deny"] = new_deny
    claude["permissions"] = perms
    write_json_file(CLAUDE_SETTINGS, claude)
    print("Synced: Claude Code (.claude/settings.json)")

    # VS Code settings (Copilot)
    vscode = read_json_file(VSCODE_SETTINGS, {})
    associations: Dict[str, str] = dict(vscode.get("files.associations", {}))
    copilot_enable: Dict[str, bool] = dict(vscode.get("github.copilot.enable", {}))

    for pattern in effective.get("protectedFiles", []):
        associations[pattern] = "copilot-restricted-file"

    copilot_enable["copilot-restricted-file"] = False

    vscode["chat.tools.terminal.autoApprove"] = merge_record(
        vscode.get("chat.tools.terminal.autoApprove", {}), effective.get("terminalAutoApprove", {}),
    )
    vscode["chat.tools.edits.autoApprove"] = merge_record(
        vscode.get("chat.tools.edits.autoApprove", {}), effective.get("editAutoApprove", {}),
    )
    vscode["files.associations"] = associations
    vscode["github.copilot.enable"] = merge_record(vscode.get("github.copilot.enable", {}), copilot_enable)

    write_json_file(VSCODE_SETTINGS, vscode)
    print("Synced: Copilot local policy (.vscode/settings.json)")

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
