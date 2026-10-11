#!/usr/bin/env python3
"""Dependency-free structural validation for the cmize-skills bundle."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from .metadata import MetadataError, bundle_version
except ImportError:  # pragma: no cover - direct script execution
    from metadata import MetadataError, bundle_version


EXPECTED_SKILLS = {
    "adversarial-review",
    "actor-critic-mode",
    "auto-review",
    "deep-research",
    "best-practices",
    "reset-cursor-vscode-macos",
}
PLUGIN_MANIFESTS = (
    "src/.claude-plugin/plugin.json",
    "src/.codex-plugin/plugin.json",
    "src/.cursor-plugin/plugin.json",
)
MARKETPLACE_MANIFESTS = (
    ".claude-plugin/marketplace.json",
    ".agents/plugins/marketplace.json",
    ".cursor-plugin/marketplace.json",
)
CURSOR_PLUGIN_KEYS = {
    "name",
    "displayName",
    "description",
    "version",
    "minClientVersions",
    "author",
    "publisher",
    "homepage",
    "repository",
    "license",
    "logo",
    "keywords",
    "category",
    "tags",
    "commands",
    "agents",
    "skills",
    "rules",
    "hooks",
    "variables",
    "mcpServers",
}
CODEX_MARKETPLACE_KEYS = {"name", "interface", "plugins"}
CODEX_MARKETPLACE_PLUGIN_KEYS = {"name", "source", "policy", "category"}
CURSOR_MARKETPLACE_KEYS = {"name", "owner", "metadata", "plugins"}
CURSOR_MARKETPLACE_PLUGIN_KEYS = {"name", "source", "description", "minClientVersions"}
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LINK_RE = re.compile(r"\]\(([^)\s]+)(?:\s+['\"][^'\"]*['\"])?\)")
MACHINE_PATH_RE = re.compile(
    r"(?:/Users/|/home/|/private/(?:var|tmp)/|/(?:tmp|var)/|"
    r"~/(?:\.codex|\.claude|\.cursor|\.agents|\.config)|"
    r"(?<![A-Za-z])[A-Za-z]:[\\/]|\\\\)"
)
WINDOWS_PATH_RE = re.compile(r"^(?:[A-Za-z]:[\\/]|\\\\)")


def _read_json(path: Path, errors: list[str]) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing JSON manifest: {path.relative_to(path.parents[1])}")
        return None
    except json.JSONDecodeError as exc:
        errors.append(f"invalid JSON in {path}: {exc}")
        return None
    if not isinstance(value, dict):
        errors.append(f"JSON root must be an object: {path}")
        return None
    return value


def parse_frontmatter(text: str) -> tuple[dict[str, str], str | None]:
    """Parse the simple scalar frontmatter used by this repository."""

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, "missing opening frontmatter delimiter"
    try:
        end = lines.index("---", 1)
    except ValueError:
        return {}, "missing closing frontmatter delimiter"

    values: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip():
            continue
        if ":" not in line:
            return {}, f"invalid frontmatter line: {line!r}"
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            return {}, f"empty frontmatter key: {line!r}"
        if value.startswith(">") or value.startswith("|"):
            return {}, f"multiline frontmatter is not supported: {key}"
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key] = value
    return values, None


def _relative_display(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def validate_skill(skill_dir: Path, root: Path) -> list[str]:
    errors: list[str] = []
    skill_file = skill_dir / "SKILL.md"
    display = _relative_display(skill_file, root)
    if not skill_file.is_file():
        return [f"missing skill file: {display}"]

    text = skill_file.read_text(encoding="utf-8")
    if len(text.splitlines()) >= 500:
        errors.append(f"{display} must be under 500 lines")
    frontmatter, frontmatter_error = parse_frontmatter(text)
    if frontmatter_error:
        errors.append(f"{display}: {frontmatter_error}")
    else:
        name = frontmatter.get("name", "")
        description = frontmatter.get("description", "")
        if not NAME_RE.fullmatch(name):
            errors.append(f"{display}: invalid skill name {name!r}")
        if name != skill_dir.name:
            errors.append(
                f"{display}: frontmatter name {name!r} does not match directory {skill_dir.name!r}"
            )
        if not description.strip():
            errors.append(f"{display}: description must be non-empty")
        if len(description) > 1024:
            errors.append(f"{display}: description is unexpectedly long")
        if frontmatter.get("disable-model-invocation") not in (None, "true", "false"):
            errors.append(f"{display}: disable-model-invocation must be true or false")

    for path in skill_dir.rglob("*"):
        if not path.is_file():
            continue
        if "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
            continue
        try:
            contents = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"{_relative_display(path, root)} is not UTF-8 text")
            continue
        if MACHINE_PATH_RE.search(contents):
            errors.append(
                f"{_relative_display(path, root)} contains a machine-specific absolute path"
            )
        for match in LINK_RE.finditer(contents):
            target = match.group(1)
            if (
                target.startswith(("http://", "https://", "mailto:", "#"))
                or target.startswith("data:")
            ):
                continue
            if target.startswith(("/", "~")) or WINDOWS_PATH_RE.match(target):
                errors.append(
                    f"{_relative_display(path, root)} contains a non-package-relative link: {target}"
                )
                continue
            target_path = (path.parent / target.split("#", 1)[0].split("?", 1)[0]).resolve()
            package_skills_root = (root / "src/skills").resolve()
            if not package_skills_root.is_dir():
                package_skills_root = root.resolve()
            if not _is_within(target_path, package_skills_root):
                errors.append(
                    f"{_relative_display(path, root)} links outside the package skill tree: {target}"
                )
                continue
            if not target_path.exists():
                errors.append(
                    f"{_relative_display(path, root)} links to missing path: {target}"
                )
    return errors


def _validate_plugin_manifest(
    path: Path,
    root: Path,
    errors: list[str],
    expected_version: str | None = None,
) -> None:
    data = _read_json(path, errors)
    if data is None:
        return
    display = _relative_display(path, root)
    if data.get("name") != "cmize-skills":
        errors.append(f"{display}: name must be cmize-skills")
    if expected_version is not None and data.get("version") != expected_version:
        errors.append(
            f"{display}: version must match canonical marketplace metadata.version "
            f"({expected_version})"
        )
    if not isinstance(data.get("description"), str) or not data["description"].strip():
        errors.append(f"{display}: description must be non-empty")
    if data.get("skills") != "./skills":
        errors.append(f"{display}: skills must point to ./skills")
    if not isinstance(data.get("author"), dict) or not data["author"].get("name"):
        errors.append(f"{display}: author.name must be present")
    if path == root / "src/.cursor-plugin/plugin.json":
        unexpected = sorted(set(data) - CURSOR_PLUGIN_KEYS)
        if unexpected:
            errors.append(
                f"{display}: unsupported Cursor manifest keys: {', '.join(unexpected)}"
            )
        author = data.get("author")
        if isinstance(author, dict):
            unexpected_author = sorted(set(author) - {"name", "email"})
            if unexpected_author:
                errors.append(
                    f"{display}: unsupported Cursor author keys: "
                    f"{', '.join(unexpected_author)}"
                )


def _validate_marketplace(
    path: Path,
    root: Path,
    errors: list[str],
    expected_version: str | None = None,
) -> None:
    data = _read_json(path, errors)
    if data is None:
        return
    display = _relative_display(path, root)
    if data.get("name") != "cmize-skills":
        errors.append(f"{display}: name must be cmize-skills")
    is_claude = path == root / ".claude-plugin/marketplace.json"
    if is_claude:
        metadata = data.get("metadata")
        if (
            expected_version is not None
            and (
                not isinstance(metadata, dict)
                or metadata.get("version") != expected_version
            )
        ):
            errors.append(
                f"{display}: metadata.version must match canonical marketplace version "
                f"({expected_version})"
            )
    is_codex = path == root / ".agents/plugins/marketplace.json"
    if not is_codex and (
        not isinstance(data.get("owner"), dict) or not data["owner"].get("name")
    ):
        errors.append(f"{display}: owner.name must be present")
    plugins = data.get("plugins")
    if not isinstance(plugins, list) or len(plugins) != 1:
        errors.append(f"{display}: plugins must contain exactly one entry")
        return
    plugin = plugins[0]
    if not isinstance(plugin, dict) or plugin.get("name") != "cmize-skills":
        errors.append(f"{display}: plugin entry must be cmize-skills")
        return
    source = plugin.get("source")
    if isinstance(source, str):
        source_path = source
    elif isinstance(source, dict):
        source_path = source.get("path")
    else:
        source_path = None
    if source_path != "./src":
        errors.append(f"{display}: plugin source must point to ./src")
    if (
        is_claude
        and expected_version is not None
        and plugin.get("version") != expected_version
    ):
        errors.append(
            f"{display}: plugin version must match canonical marketplace metadata.version "
            f"({expected_version})"
        )
    if is_codex:
        unexpected = sorted(set(data) - CODEX_MARKETPLACE_KEYS)
        if unexpected:
            errors.append(
                f"{display}: unsupported Codex marketplace keys: {', '.join(unexpected)}"
            )
        interface = data.get("interface")
        if not isinstance(interface, dict) or not interface.get("displayName"):
            errors.append(f"{display}: Codex interface.displayName must be present")
        if not isinstance(source, dict) or source.get("source") != "local":
            errors.append(f"{display}: Codex local source must declare source=local")
        unexpected_plugin = sorted(set(plugin) - CODEX_MARKETPLACE_PLUGIN_KEYS)
        if unexpected_plugin:
            errors.append(
                f"{display}: unsupported Codex plugin-entry keys: "
                f"{', '.join(unexpected_plugin)}"
            )
        policy = plugin.get("policy")
        if not isinstance(policy, dict):
            errors.append(f"{display}: Codex plugin policy must be present")
        else:
            if policy.get("installation") != "AVAILABLE":
                errors.append(f"{display}: Codex installation policy must be AVAILABLE")
            if policy.get("authentication") != "ON_INSTALL":
                errors.append(
                    f"{display}: Codex authentication policy must be ON_INSTALL"
                )
        if plugin.get("category") != "Productivity":
            errors.append(f"{display}: Codex plugin category must be Productivity")
    if path == root / ".cursor-plugin/marketplace.json":
        unexpected = sorted(set(data) - CURSOR_MARKETPLACE_KEYS)
        if unexpected:
            errors.append(
                f"{display}: unsupported Cursor marketplace keys: {', '.join(unexpected)}"
            )
        owner = data.get("owner")
        if isinstance(owner, dict):
            unexpected_owner = sorted(set(owner) - {"name", "email"})
            if unexpected_owner:
                errors.append(
                    f"{display}: unsupported Cursor owner keys: "
                    f"{', '.join(unexpected_owner)}"
                )
        if not isinstance(source, str):
            errors.append(f"{display}: Cursor marketplace source must be a string")
        unexpected_plugin = sorted(set(plugin) - CURSOR_MARKETPLACE_PLUGIN_KEYS)
        if unexpected_plugin:
            errors.append(
                f"{display}: unsupported Cursor plugin-entry keys: "
                f"{', '.join(unexpected_plugin)}"
            )


def _validate_codex_policy(root: Path, errors: list[str]) -> None:
    expected = {
        root / "src/skills/auto-review/agents/openai.yaml": False,
        root / "src/skills/actor-critic-mode/agents/openai.yaml": False,
        root / "src/skills/deep-research/agents/openai.yaml": True,
        root / "src/skills/reset-cursor-vscode-macos/agents/openai.yaml": False,
    }
    for path, expected_value in expected.items():
        if not path.is_file():
            errors.append(f"missing Codex metadata: {_relative_display(path, root)}")
            continue
        text = path.read_text(encoding="utf-8")
        if "policy:" not in text or "allow_implicit_invocation:" not in text:
            errors.append(f"{_relative_display(path, root)} lacks invocation policy")
            continue
        actual = re.search(r"allow_implicit_invocation:\s*(true|false)\s*$", text, re.MULTILINE)
        if actual is None or (actual.group(1) == "true") != expected_value:
            errors.append(
                f"{_relative_display(path, root)} has unexpected allow_implicit_invocation value"
            )


def validate_repository(root: Path) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    try:
        expected_version = bundle_version(root)
    except MetadataError as exc:
        errors.append(str(exc))
        expected_version = None
    skills_root = root / "src/skills"
    if not skills_root.is_dir():
        return ["missing src/skills directory"]

    discovered = {path.name for path in skills_root.iterdir() if path.is_dir()}
    if discovered != EXPECTED_SKILLS:
        errors.append(
            f"src/skills directories must be {sorted(EXPECTED_SKILLS)}, found {sorted(discovered)}"
        )
    for skill_name in sorted(EXPECTED_SKILLS):
        errors.extend(validate_skill(skills_root / skill_name, root))

    for relative_path in PLUGIN_MANIFESTS:
        _validate_plugin_manifest(root / relative_path, root, errors, expected_version)
    for relative_path in MARKETPLACE_MANIFESTS:
        _validate_marketplace(root / relative_path, root, errors, expected_version)
    _validate_codex_policy(root, errors)

    skill_files = {
        path.resolve()
        for path in root.rglob("SKILL.md")
        if path.is_file()
    }
    expected_skill_files = {
        (skills_root / name / "SKILL.md").resolve() for name in EXPECTED_SKILLS
    }
    if skill_files != expected_skill_files:
        errors.append("SKILL.md files must exist only in the canonical src/skills tree")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root (default: this repository)",
    )
    args = parser.parse_args(argv)
    errors = validate_repository(args.root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"{len(errors)} validation error(s)", file=sys.stderr)
        return 1
    print("cmize-skills validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
