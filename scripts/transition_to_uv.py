#!/usr/bin/env python3
"""Migrate pyproject.toml from Poetry to uv, then self-clean."""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


def remove_section(content: str, section_name: str) -> str:
    """Remove a TOML section header and its key-value lines."""
    lines = content.splitlines(keepends=True)
    result: list[str] = []
    skipping = False
    header = f"[{section_name}]"
    for line in lines:
        if line.strip() == header:
            skipping = True
            continue
        if skipping and line.strip().startswith("["):
            skipping = False
        if not skipping:
            result.append(line)
    return "".join(result)


def update_build_system(content: str) -> str:
    """Replace poetry-core build system with hatchling."""
    content = re.sub(
        r'requires\s*=\s*\["poetry-core[^"]*"\]',
        'requires = ["hatchling"]',
        content,
    )
    content = re.sub(
        r'build-backend\s*=\s*"poetry\.core\.masonry\.api"',
        'build-backend = "hatchling.build"',
        content,
    )
    return content


def extract_poetry_packages(content: str) -> list[str]:
    """Extract package paths from the [tool.poetry] packages key."""
    packages: list[str] = []
    in_poetry = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped == "[tool.poetry]":
            in_poetry = True
        elif in_poetry and stripped.startswith("["):
            break
        elif in_poetry and "packages" in stripped:
            for m in re.finditer(
                r'\{\s*include\s*=\s*"([^"]+)"(?:,\s*from\s*=\s*"([^"]+)")?\s*\}',
                stripped,
            ):
                name, from_dir = m.group(1), m.group(2)
                packages.append(f"{from_dir}/{name}" if from_dir else name)
    return packages


def insert_hatch_section(content: str, packages: list[str]) -> str:
    """Insert [tool.hatch.build.targets.wheel] after the [build-system] block."""
    if "[tool.hatch.build.targets.wheel]" in content:
        return content
    packages_str = ", ".join(f'"{p}"' for p in packages)
    hatch_block = f"[tool.hatch.build.targets.wheel]\n" f"packages = [{packages_str}]\n"
    lines = content.splitlines(keepends=True)
    result: list[str] = []
    in_build_system = False
    inserted = False
    for line in lines:
        if line.strip() == "[build-system]":
            in_build_system = True
        elif in_build_system and line.strip().startswith("[") and not inserted:
            result.append(hatch_block + "\n")
            in_build_system = False
            inserted = True
        result.append(line)
    if in_build_system and not inserted:
        result.append("\n" + hatch_block)
    return "".join(result)


def add_poethepoet_to_dev(content: str) -> str:
    """Add poethepoet to the [dependency-groups] dev list."""
    if "poethepoet" in content:
        return content
    match = re.search(r"dev\s*=\s*\[(.*?)\]", content, flags=re.DOTALL)
    if not match:
        return content
    items = re.findall(r'"[^"]+"', match.group(1))
    all_items = ['"poethepoet>=0.34.0"'] + items
    new_list = "[\n" + "".join(f"    {item},\n" for item in all_items) + "]"
    return content[: match.start()] + f"dev = {new_list}" + content[match.end() :]


def remove_script_key(content: str, key: str) -> str:
    """Remove a single key-value line from [project.scripts]."""
    lines = content.splitlines(keepends=True)
    result: list[str] = []
    in_scripts = False
    for line in lines:
        if line.strip() == "[project.scripts]":
            in_scripts = True
        elif in_scripts and line.strip().startswith("["):
            in_scripts = False
        if in_scripts and line.strip().startswith(f"{key}"):
            continue
        result.append(line)
    return "".join(result)


def delete_if_exists(path: Path) -> None:
    if path.exists():
        path.unlink()
        print(f"Deleted {path.name}")


    # kept for backwards compatibility; prefer using `main()` below
    return


def migrate_pyproject_content(content: str) -> str:
    """Perform the migration transforms on a pyproject.toml content string and return the new content."""
    packages = extract_poetry_packages(content)

    content = remove_section(content, "tool.poetry.requires-plugins")
    content = update_build_system(content)
    if packages:
        content = insert_hatch_section(content, packages)
    content = remove_section(content, "tool.poetry")
    content = add_poethepoet_to_dev(content)
    content = remove_script_key(content, "transition-to-uv")

    return content


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint. Defaults to operating on `pyproject.toml` in the repo root.

    Args:
        argv: Optional list of command-line arguments for testing.

    Returns:
        Exit code (0 on success).
    """
    from argparse import ArgumentParser

    parser = ArgumentParser(description="Migrate pyproject.toml from Poetry to uv.")
    parser.add_argument(
        "--input",
        "-i",
        default=str(ROOT / "pyproject.toml"),
        help="Path to the input pyproject.toml",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Path to write the migrated pyproject.toml (defaults to input path)",
    )
    parser.add_argument(
        "--no-delete",
        action="store_true",
        help="Don't delete poetry.lock or poetry.toml (useful for tests)",
    )

    args = parser.parse_args(argv)

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: {input_path} not found", file=sys.stderr)
        return 1

    content = input_path.read_text(encoding="utf-8")
    new_content = migrate_pyproject_content(content)

    output_path = Path(args.output) if args.output else input_path
    output_path.write_text(new_content, encoding="utf-8")
    print(f"{output_path.name} migrated to uv.")

    if not args.no_delete:
        delete_if_exists(ROOT / "poetry.lock")
        delete_if_exists(ROOT / "poetry.toml")

    print("Update complete. ⚠️ Please review changes.")
    print(
        "Next steps:\n"
        "1. Remove .venv and this migration script.\n"
        "2. Run 'uv sync' to install dependencies and generate the new lockfile.\n"
        "3. Review changes, test your project to ensure everything works as expected.\n"
        "4. Commit the changes with a message like 'chore: Migrate from Poetry to uv'."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
