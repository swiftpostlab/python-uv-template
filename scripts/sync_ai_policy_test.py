"""Tests for sync_ai_policy."""

from importlib import util
from pathlib import Path
from types import ModuleType
from unittest.mock import patch
from typing import cast


def load_sync_ai_policy_module() -> ModuleType:
    module_path = Path(__file__).with_name("sync_ai_policy.py")
    spec = util.spec_from_file_location("sync_ai_policy", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load sync_ai_policy.py")

    module = util.module_from_spec(spec)
    loader = cast(object, spec.loader)
    exec_module = getattr(loader, "exec_module", None)
    if exec_module is None or not callable(exec_module):
        raise RuntimeError("sync_ai_policy.py loader cannot execute the module")

    exec_module(module)
    return module


sync_ai_policy = load_sync_ai_policy_module()


def test_apply_policy_to_vscode_settings_replaces_managed_entries() -> None:
    policy = {
        "protectedFiles": ["*.env"],
        "terminalAutoApprove": {"/^uv run poe lint$/": True},
        "editAutoApprove": {"**/*.py": True},
    }
    vscode = {
        "chat.tools.terminal.autoApprove": {"old": True},
        "chat.tools.edits.autoApprove": {"old": True},
        "files.associations": {
            "stale": "copilot-restricted-file",
            "*.txt": "plaintext",
        },
        "github.copilot.enable": {"other-language": True},
    }

    updated = sync_ai_policy.apply_policy_to_vscode_settings(vscode, policy)

    assert updated["chat.tools.terminal.autoApprove"] == {"/^uv run poe lint$/": True}
    assert updated["chat.tools.edits.autoApprove"] == {"**/*.py": True}
    assert updated["files.associations"] == {
        "*.txt": "plaintext",
        "*.env": "copilot-restricted-file",
    }
    assert updated["github.copilot.enable"] == {
        "other-language": True,
        "copilot-restricted-file": False,
    }


def test_apply_policy_to_claude_settings_replaces_managed_read_rules() -> None:
    policy = {"protectedFiles": ["*.env", "secrets/"]}
    claude = {
        "permissions": {
            "deny": [
                "Read(old-secret)",
                "Bash(rm -rf /)",
            ],
        },
    }

    updated = sync_ai_policy.apply_policy_to_claude_settings(claude, policy)

    assert updated["permissions"]["deny"] == [
        "Bash(rm -rf /)",
        "Read(*.env)",
        "Read(secrets/)",
    ]


def test_import_policy_from_vscode_replaces_policy_approval_maps() -> None:
    policy = {
        "terminalAutoApprove": {"stale": True},
        "editAutoApprove": {"old": False},
    }

    with patch.object(sync_ai_policy, "read_json_file") as mock_read_json_file:
        mock_read_json_file.return_value = {
            "chat.tools.terminal.autoApprove": {"/^uv run poe test$/": True},
            "chat.tools.edits.autoApprove": {"**/*.py": True},
        }

        updated = sync_ai_policy.import_policy_from_vscode(policy)

    assert updated["terminalAutoApprove"] == {"/^uv run poe test$/": True}
    assert updated["editAutoApprove"] == {"**/*.py": True}


def test_import_policy_from_vscode_clears_missing_policy_approval_maps() -> None:
    policy = {
        "terminalAutoApprove": {"stale": True},
        "editAutoApprove": {"old": False},
    }

    with patch.object(sync_ai_policy, "read_json_file") as mock_read_json_file:
        mock_read_json_file.return_value = {}

        updated = sync_ai_policy.import_policy_from_vscode(policy)

    assert updated["terminalAutoApprove"] == {}
    assert updated["editAutoApprove"] == {}
