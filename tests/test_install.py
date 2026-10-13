from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from agent_files import install as install_module
from agent_files.install import InstallError, install, smoke
from agent_files.repo import find_repo_root

REPO = find_repo_root()


@pytest.fixture
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("HOME", str(tmp_path))
    return tmp_path


def test_install_writes_real_file_links_hosts_and_uninstall_restores(home: Path) -> None:
    src = (REPO / "agents" / "AGENTS.md").read_text(encoding="utf-8")
    old_target = home / "dotfiles" / "AGENTS.md"
    old_target.parent.mkdir()
    old_target.write_text("old\n", encoding="utf-8")
    (home / "AGENTS.md").symlink_to(old_target)
    (home / ".claude").mkdir()
    (home / ".claude" / "CLAUDE.md").write_text("claude-only\n", encoding="utf-8")

    install(repo=REPO)

    home_file = home / "AGENTS.md"
    assert not home_file.is_symlink()
    assert home_file.read_text(encoding="utf-8") == src
    assert old_target.read_text(encoding="utf-8") == "old\n"
    claude = home / ".claude" / "CLAUDE.md"
    assert claude.is_symlink() and Path(os.readlink(claude)) == home_file
    assert not (home / ".codex").exists()
    for dest in (home / ".agents" / "skills", home / ".claude" / "skills"):
        assert (dest / "best-practices" / "SKILL.md").is_file()
    smoke(repo=REPO)

    assert all(line.startswith(("unchanged", "skip")) for line in install(repo=REPO))

    install(repo=REPO, uninstall=True)

    assert home_file.is_symlink() and Path(os.readlink(home_file)) == old_target
    assert not claude.is_symlink()
    assert claude.read_text(encoding="utf-8") == "claude-only\n"
    assert not (home / ".agents" / "skills" / "best-practices").exists()


def test_existing_skill_folders_are_backed_up_outside_skill_dirs_and_stale_copies_removed(home: Path) -> None:
    skills = home / ".agents" / "skills"
    shutil.copytree(REPO / "skills" / "auto-review", skills / "auto-review")
    (skills / "best-practices").mkdir(parents=True)
    (skills / "best-practices" / "SKILL.md").write_text("my local edit\n", encoding="utf-8")
    stale = home / ".cursor" / "skills" / "best-practices"
    shutil.copytree(REPO / "skills" / "best-practices", stale)
    (home / ".agent-files-install-manifest.json").write_text(
        json.dumps({"copied": [{"src": "x", "dest": str(stale)}]}), encoding="utf-8"
    )

    install(repo=REPO)

    assert not stale.exists()
    backups = sorted(p.name for p in (home / ".agent-files-backups").iterdir())
    assert backups == ["agents_skills_auto-review", "agents_skills_best-practices"]
    smoke(repo=REPO)

    install(repo=REPO, uninstall=True)

    assert (skills / "best-practices" / "SKILL.md").read_text(encoding="utf-8") == "my local edit\n"
    assert (skills / "auto-review" / "SKILL.md").is_file()
    assert not (skills / "deep-research").exists()


def test_install_stopped_before_backup_or_uninstall_stopped_before_save_never_loses_the_original(
    home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mine = home / ".agents" / "skills" / "best-practices"
    mine.mkdir(parents=True)
    (mine / "SKILL.md").write_text("mine\n", encoding="utf-8")
    real_clear = install_module._clear

    def crash_on_mine(record: install_module.InstructionRecord) -> None:
        if record["dest"] == str(mine):
            raise OSError("stopped")
        real_clear(record)

    with monkeypatch.context() as m:
        m.setattr(install_module, "_clear", crash_on_mine)
        with pytest.raises(OSError):
            install(repo=REPO)
    install(repo=REPO)

    real_save = install_module._Manifest.save
    calls = {"n": 0}

    def crash_after_restoring_mine(self: install_module._Manifest) -> None:
        if str(mine) not in self.copied and not calls["n"]:
            calls["n"] += 1
            raise OSError("stopped")
        real_save(self)

    with monkeypatch.context() as m:
        m.setattr(install_module._Manifest, "save", crash_after_restoring_mine)
        with pytest.raises(OSError):
            install(repo=REPO, uninstall=True)
    assert calls["n"] == 1
    assert (mine / "SKILL.md").read_text(encoding="utf-8") == "mine\n"
    install(repo=REPO)
    install(repo=REPO, uninstall=True)

    assert (mine / "SKILL.md").read_text(encoding="utf-8") == "mine\n"


def test_skipped_host_keeps_records_and_foreign_symlinked_skill_is_replaced(home: Path) -> None:
    foreign = home / "other-repo"
    (foreign / "best-practices").mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(foreign)], check=True)
    subprocess.run(["git", "-C", str(foreign), "remote", "add", "origin", "https://github.com/x/y.git"], check=True)
    skills = home / ".agents" / "skills"
    skills.mkdir(parents=True)
    (skills / "best-practices").symlink_to(foreign / "best-practices")
    (home / ".claude").mkdir()

    install(repo=REPO)
    assert not (skills / "best-practices").is_symlink()
    shutil.rmtree(home / ".claude")
    install(repo=REPO)
    install(repo=REPO, uninstall=True)

    assert Path(os.readlink(skills / "best-practices")) == foreign / "best-practices"
    assert not (home / "AGENTS.md").exists()


def test_smoke_rejects_extra_entries_in_an_installed_skill(home: Path) -> None:
    install(repo=REPO)
    (home / ".agents" / "skills" / "best-practices" / "extra").mkdir()

    with pytest.raises(InstallError, match="best-practices differs"):
        smoke(repo=REPO)


def test_dry_run_changes_nothing_and_smoke_rejects_symlinked_home_file(home: Path) -> None:
    (home / "AGENTS.md").symlink_to(REPO / "agents" / "AGENTS.md")
    (home / ".claude").mkdir()

    install(repo=REPO, dry_run=True)

    assert (home / "AGENTS.md").is_symlink()
    assert not (home / ".claude" / "CLAUDE.md").exists()
    assert not (home / ".agents").exists()
    assert not (home / ".agent-files-install-manifest.json").exists()
    with pytest.raises(InstallError, match="not a regular file"):
        smoke(repo=REPO)


def test_failed_install_keeps_restore_record_for_retry_and_uninstall(
    home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (home / "AGENTS.md").write_text("mine\n", encoding="utf-8")
    (home / ".claude").mkdir()

    def fail(*_args: object, **_kwargs: object) -> None:
        raise OSError("disk full")

    with monkeypatch.context() as m:
        m.setattr(shutil, "copytree", fail)
        with pytest.raises(OSError):
            install(repo=REPO)
    install(repo=REPO)
    install(repo=REPO, uninstall=True)

    assert (home / "AGENTS.md").read_text(encoding="utf-8") == "mine\n"
    assert not (home / ".claude" / "CLAUDE.md").exists()
