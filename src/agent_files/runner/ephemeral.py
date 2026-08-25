"""Ephemeral workspaces under the cache directory."""

from __future__ import annotations

import shutil
import subprocess
import uuid
from pathlib import Path

from agent_files.config import AppConfig
from agent_files.models.run import RunSpec
from agent_files.repo import find_repo_root


def new_run_dir(config: AppConfig, run_id: str | None = None) -> Path:
    rid = run_id or str(uuid.uuid4())
    path = config.cache_path() / "runs" / rid
    path.mkdir(parents=True, exist_ok=True)
    return path


def copy_fixture(src: Path, dest: Path) -> None:
    if src.is_file():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        return
    shutil.copytree(src, dest, dirs_exist_ok=True)


def overlay_tree(src: Path, dest: Path) -> None:
    if not src.exists():
        return
    copy_fixture(src, dest)


def git_init(workspace: Path) -> None:
    subprocess.run(
        ["git", "init", "-q"],
        cwd=workspace,
        check=True,
        capture_output=True,
    )


def repo_porcelain(repo: Path) -> str:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return ""
    return result.stdout


def assert_repo_clean(repo: Path | None = None) -> None:
    root = repo or find_repo_root()
    dirty = repo_porcelain(root)
    if dirty.strip():
        raise RuntimeError(f"agent-files git is dirty after eval:\n{dirty}")


def crowded_skill_ids(plugin_skills: Path, exclude: str | None) -> list[str]:
    ids: list[str] = []
    if not plugin_skills.is_dir():
        return ids
    for child in sorted(plugin_skills.iterdir()):
        if not child.is_dir():
            continue
        if exclude and child.name == exclude:
            continue
        ids.append(child.name)
    return ids


def assemble_plugin(
    repo: Path,
    *,
    artifact: str,
    dest: Path,
    crowded: bool,
) -> list[str]:
    """Build a Cursor/Codex plugin directory. Exclude the skill under test when crowded."""
    skills_dest = dest / "skills"
    skills_dest.mkdir(parents=True, exist_ok=True)
    (dest / "plugin.json").write_text(
        '{"name":"agent-files-eval","version":"0.0.0","skills":"./skills"}\n',
        encoding="utf-8",
    )
    (dest / ".cursor-plugin").mkdir(parents=True, exist_ok=True)
    (dest / ".cursor-plugin" / "plugin.json").write_text(
        '{"name":"agent-files-eval","version":"0.0.0","description":"eval plugin","skills":"./skills"}\n',
        encoding="utf-8",
    )
    if artifact == "review":
        for name in ("auto-review", "adversarial-review"):
            src = (repo / "skills" / name)
            if src.is_dir():
                copy_fixture(src, skills_dest / name)
        return crowded_skill_ids(skills_dest, exclude=None)
    exclude: str | None = None
    if artifact.startswith("skills/"):
        exclude = artifact.split("/", 1)[1]
    imported = repo / "skills"
    if crowded:
        crowded_root = imported / "_fixtures" / "crowded" / "skills"
        if crowded_root.is_dir():
            for child in crowded_root.iterdir():
                if child.name == exclude:
                    continue
                copy_fixture(child, skills_dest / child.name)
        if imported.is_dir():
            for child in imported.iterdir():
                if not child.is_dir() or child.name.startswith("_"):
                    continue
                if child.name == exclude:
                    continue
                if (skills_dest / child.name).exists():
                    continue
                copy_fixture(child, skills_dest / child.name)
    elif imported.is_dir() and exclude is None:
        for child in imported.iterdir():
            if child.is_dir() and not child.name.startswith("_"):
                copy_fixture(child, skills_dest / child.name)
    elif imported.is_dir() and exclude is not None:
        target = imported / exclude
        if target.is_dir():
            copy_fixture(target, skills_dest / exclude)
    return crowded_skill_ids(skills_dest, exclude=None)


def prepare_workspace(
    config: AppConfig,
    spec: RunSpec,
    repo: Path,
    run_id: str,
) -> tuple[Path, Path, list[str]]:
    run_dir = new_run_dir(config, run_id)
    workspace = run_dir / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    for rel in spec.fixture_relpaths:
        src = repo / rel
        if src.exists():
            copy_fixture(src, workspace)
    git_init(workspace)
    if spec.overlay_root is not None:
        overlay = spec.overlay_root
        if overlay.is_file() and overlay.name == "AGENTS.md":
            shutil.copy2(overlay, workspace / "AGENTS.md")
        elif overlay.is_dir():
            overlay_tree(overlay, workspace)
    plugin_dir = run_dir / "plugin"
    fixture_ids = assemble_plugin(
        repo,
        artifact=spec.artifact,
        dest=plugin_dir,
        crowded=spec.crowded,
    )
    return workspace, plugin_dir, fixture_ids
