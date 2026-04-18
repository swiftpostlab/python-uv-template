"""Synchronize the shared AI policy into agent-specific config files."""

from __future__ import annotations

from argparse import ArgumentParser
from collections.abc import Callable
from importlib import import_module
from json import JSONDecodeError
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, cast

ROOT = Path(__file__).resolve().parent.parent.parent
AI_POLICY = ROOT / ".ai-policy.json"
AI_EXCLUDE = ROOT / ".aiexclude"
VSCODE_SETTINGS = ROOT / ".vscode" / "settings.json"
CLAUDE_SETTINGS = ROOT / ".claude" / "settings.json"

TerminalApprovalRule = Dict[str, Union[bool, Any]]
TerminalApprovalSetting = Union[bool, TerminalApprovalRule]

AiPolicy = Dict[str, Any]
VscodeSettings = Dict[str, Any]
JsonLoader = Callable[[str], Any]


def load_optional_json5_loader() -> Optional[JsonLoader]:
    try:
        json5_module = import_module("json5")
    except ModuleNotFoundError:
        return None

    loads = getattr(json5_module, "loads", None)
    return loads if callable(loads) else None


JSON5_LOADS = load_optional_json5_loader()


def read_json_file(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback

    text = path.read_text(encoding="utf-8")
    if JSON5_LOADS is not None:
        try:
            return JSON5_LOADS(text)
        except Exception:
            pass

    try:
        return json.loads(text)
    except JSONDecodeError:
        cleaned = _strip_jsonc(text)
        return json.loads(cleaned)


def _strip_jsonc(text: str) -> str:
    def remove_comments(content: str) -> str:
        out: List[str] = []
        index = 0
        length = len(content)
        in_string = False
        quote_char = ""

        while index < length:
            char = content[index]

            if in_string:
                out.append(char)
                if char == "\\":
                    if index + 1 < length:
                        out.append(content[index + 1])
                        index += 2
                        continue
                elif char == quote_char:
                    in_string = False
                index += 1
                continue

            if char in {'"', "'"}:
                in_string = True
                quote_char = char
                out.append(char)
                index += 1
                continue

            if char == "/" and index + 1 < length and content[index + 1] == "/":
                index += 2
                while index < length and content[index] != "\n":
                    index += 1
                continue

            if char == "/" and index + 1 < length and content[index + 1] == "*":
                index += 2
                while index + 1 < length and not (content[index] == "*" and content[index + 1] == "/"):
                    index += 1
                index += 2 if index + 1 < length else 1
                continue

            out.append(char)
            index += 1

        return "".join(out)

    return re.sub(r",\s*(?=[}\]])", "", remove_comments(text))


def write_json_file(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file_handle:
        json.dump(data, file_handle, indent=2)
        file_handle.write("\n")


def write_text_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


T = Any


def get_string_list(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []

    items = cast(List[Any], value)
    return [item for item in items if isinstance(item, str)]


def get_string_mapping(value: Any) -> Dict[str, str]:
    if not isinstance(value, dict):
        return {}

    items = cast(Dict[Any, Any], value)
    return {key: item for key, item in items.items() if isinstance(key, str) and isinstance(item, str)}


def get_boolean_mapping(value: Any) -> Dict[str, bool]:
    if not isinstance(value, dict):
        return {}

    items = cast(Dict[Any, Any], value)
    return {key: item for key, item in items.items() if isinstance(key, str) and isinstance(item, bool)}


def get_terminal_approval_mapping(value: Any) -> Dict[str, TerminalApprovalSetting]:
    if not isinstance(value, dict):
        return {}

    items = cast(Dict[Any, Any], value)
    return {key: item for key, item in items.items() if isinstance(key, str)}


def get_protected_files(policy: AiPolicy) -> List[str]:
    return get_string_list(policy.get("protectedFiles", []))


def get_excluded_files(policy: AiPolicy) -> List[str]:
    return get_string_list(policy.get("excludedFiles", []))


def apply_policy_to_claude_settings(claude: Dict[str, Any], policy: AiPolicy) -> Dict[str, Any]:
    updated = dict(claude)
    permissions = dict(claude.get("permissions", {})) if isinstance(claude.get("permissions"), dict) else {}
    existing_deny = get_string_list(permissions.get("deny", []))
    unmanaged_deny = [entry for entry in existing_deny if not entry.startswith("Read(")]
    permissions["deny"] = unmanaged_deny + [f"Read({pattern})" for pattern in get_protected_files(policy)]
    updated["permissions"] = permissions
    return updated


def apply_policy_to_vscode_settings(vscode: VscodeSettings, policy: AiPolicy) -> VscodeSettings:
    updated = dict(vscode)
    associations = get_string_mapping(updated.get("files.associations", {}))
    associations = {
        pattern: language
        for pattern, language in associations.items()
        if language != "copilot-restricted-file"
    }
    for pattern in get_protected_files(policy):
        associations[pattern] = "copilot-restricted-file"

    copilot_enable = get_boolean_mapping(updated.get("github.copilot.enable", {}))
    copilot_enable["copilot-restricted-file"] = False

    updated["chat.tools.terminal.autoApprove"] = get_terminal_approval_mapping(
        policy.get("terminalAutoApprove", {}),
    )
    updated["chat.tools.edits.autoApprove"] = get_boolean_mapping(policy.get("editAutoApprove", {}))
    updated["files.associations"] = associations
    updated["github.copilot.enable"] = copilot_enable
    return updated


def build_ai_exclude_content(policy: AiPolicy) -> str:
    lines: List[str] = [
        "# ============================================================================== ",
        "# AI EXCLUSION FILE",
        "# Generated from .ai-policy.json",
        "# Protected files are sensitive; excluded files are mostly noise or generated output.",
        "# ==============================================================================" ,
        "",
        "# --- 1. Protected files ---",
    ]

    lines.extend(get_protected_files(policy))
    lines.append("")
    lines.append("# --- 2. Excluded noise / generated output ---")
    lines.extend(get_excluded_files(policy))
    lines.append("")
    return "\n".join(lines)


def import_policy_from_vscode(policy: AiPolicy) -> AiPolicy:
    vscode: VscodeSettings = read_json_file(VSCODE_SETTINGS, {})
    new_policy = dict(policy)

    imported_terminal = get_terminal_approval_mapping(vscode.get("chat.tools.terminal.autoApprove", {}))
    imported_edits = get_boolean_mapping(vscode.get("chat.tools.edits.autoApprove", {}))

    if imported_terminal:
        new_policy["terminalAutoApprove"] = imported_terminal
    if imported_edits:
        new_policy["editAutoApprove"] = imported_edits
    return new_policy


def run(arguments: Optional[List[str]] = None) -> int:
    parser = ArgumentParser(description="Sync .ai-policy.json into agent-specific configuration files.")
    parser.add_argument("--import-vscode", action="store_true", help="Import VS Code approvals into .ai-policy.json first")
    args = parser.parse_args(arguments)

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

    protected_files = get_protected_files(effective)
    excluded_files = get_excluded_files(effective)

    if not protected_files and not excluded_files:
        print(".ai-policy.json has no file patterns. Nothing to sync.")
        return 0

    write_text_file(AI_EXCLUDE, build_ai_exclude_content(effective))
    print(f"Loaded {len(protected_files)} protected patterns and {len(excluded_files)} excluded patterns")
    print("Synced: Gemini (.aiexclude)")

    claude = read_json_file(CLAUDE_SETTINGS, {})
    write_json_file(CLAUDE_SETTINGS, apply_policy_to_claude_settings(claude, effective))
    print("Synced: Claude Code (.claude/settings.json)")

    vscode = read_json_file(VSCODE_SETTINGS, {})
    write_json_file(VSCODE_SETTINGS, apply_policy_to_vscode_settings(vscode, effective))
    print("Synced: Copilot local policy (.vscode/settings.json)")

    print("Done.")
    return 0


def main() -> int:
    return run()


def import_vscode_main() -> int:
    return run(["--import-vscode"])