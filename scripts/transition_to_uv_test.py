"""Tests for transition_to_uv migration.

These tests load the `transition_to_uv.py` script as a module and call the
`migrate_pyproject_content` helper with mock fixture files placed alongside
the module so tests don't touch repository files.
"""

from importlib import util
from pathlib import Path
import re


def load_transition_module():
    module_path = Path(__file__).parent / "transition_to_uv.py"
    spec = util.spec_from_file_location("transition_to_uv", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load transition_to_uv.py")

    module = util.module_from_spec(spec)
    loader = spec.loader
    exec_module = getattr(loader, "exec_module", None)
    if exec_module is None or not callable(exec_module):
        raise RuntimeError("transition_to_uv.py loader cannot execute the module")

    exec_module(module)
    return module


def normalize(text: str) -> str:
    # Remove trailing whitespace, collapse multiple blank lines, trim edges
    lines = [line.rstrip() for line in text.splitlines()]
    s = "\n".join(lines).strip()
    s = re.sub(r"\n\s*\n+", "\n\n", s)
    return s


def test_migration_matches_expected_fixture() -> None:
    module = load_transition_module()

    base = Path(__file__).parent
    input_text = (base / "mock_poetry_project.toml").read_text(encoding="utf-8")
    expected_text = (base / "expected_mock_uv_project.toml").read_text(
        encoding="utf-8"
    )

    output = module.migrate_pyproject_content(input_text)

    assert normalize(output) == normalize(expected_text)
