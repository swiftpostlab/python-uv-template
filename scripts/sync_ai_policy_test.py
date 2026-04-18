"""Tests for sync_ai_policy."""

from unittest.mock import patch

from my_project import sync_ai_policy


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

    with patch("my_project.sync_ai_policy.read_json_file") as mock_read_json_file:
        mock_read_json_file.return_value = {
            "chat.tools.terminal.autoApprove": {"/^uv run poe test$/": True},
            "chat.tools.edits.autoApprove": {"**/*.py": True},
        }

        updated = sync_ai_policy.import_policy_from_vscode(policy)

    assert updated["terminalAutoApprove"] == {"/^uv run poe test$/": True}
    assert updated["editAutoApprove"] == {"**/*.py": True}