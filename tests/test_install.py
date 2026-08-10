from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
import tempfile
import unittest
from pathlib import Path

from scripts.install import (
    InstallationError,
    build_plan,
    build_manifest,
    execute_plan,
    manifest_path,
    main,
    selected_skills,
    uninstall,
    update_install,
    _write_manifest,
)


def make_source(root: Path) -> Path:
    source = root / "src"
    for name in ("alpha", "beta"):
        skill = source / "skills" / name
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: {name} fixture.\n---\n",
            encoding="utf-8",
        )
    return source


class InstallTests(unittest.TestCase):
    def test_auto_review_selection_includes_its_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            source = make_source(Path(temp))
            # The fixture names are unrelated to the production dependency map;
            # assert the map itself through a production-shaped temporary source.
            for name in ("adversarial-review", "auto-review"):
                skill = source / "skills" / name
                skill.mkdir()
                (skill / "SKILL.md").write_text(
                    f"---\nname: {name}\ndescription: {name} fixture.\n---\n",
                    encoding="utf-8",
                )
            selected = selected_skills(source, ["auto-review"])
        self.assertEqual(selected, ["adversarial-review", "auto-review"])

    def test_dry_run_does_not_create_destination(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = make_source(root)
            destination = root / "destination"
            plan = build_plan(source, destination, ["alpha"])
            actions = execute_plan(plan, dry_run=True)
            self.assertFalse(destination.exists())
            self.assertIn("DRY-RUN copy", actions[0])

    def test_selected_skill_is_copied(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = make_source(root)
            destination = root / "destination"
            plan = build_plan(source, destination, ["alpha"])
            execute_plan(plan)
            self.assertTrue((destination / "alpha/SKILL.md").is_file())
            self.assertFalse((destination / "beta").exists())

    def test_existing_destination_requires_explicit_replace(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = make_source(root)
            destination = root / "destination"
            destination.mkdir()
            (destination / "alpha").mkdir()
            plan = build_plan(source, destination, ["alpha"])
            with self.assertRaises(InstallationError):
                execute_plan(plan)
            execute_plan(plan, replace=True)
            self.assertIn("name: alpha", (destination / "alpha/SKILL.md").read_text())

    def test_symlink_mode_points_at_canonical_skill(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = make_source(root)
            destination = root / "destination"
            plan = build_plan(source, destination, ["beta"])
            execute_plan(plan, symlink=True)
            self.assertTrue((destination / "beta").is_symlink())
            self.assertEqual(
                (destination / "beta").resolve(),
                (source / "skills/beta").resolve(),
            )

    def test_update_preserves_manifest_symlink_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = make_source(root)
            destination = root / "destination"
            plan = build_plan(source, destination, ["alpha"])
            execute_plan(plan, symlink=True)
            _write_manifest(
                manifest_path(destination),
                build_manifest(source, destination, "claude", plan, True),
            )

            update_install(
                source,
                destination,
                "claude",
                None,
                select_all=False,
                dry_run=False,
                symlink=False,
                replace=False,
            )
            self.assertTrue((destination / "alpha").is_symlink())

    def test_manifest_supports_update_and_uninstall(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = make_source(root)
            destination = root / "destination"
            plan = build_plan(source, destination, ["alpha", "beta"])
            execute_plan(plan)
            _write_manifest(
                manifest_path(destination),
                build_manifest(source, destination, "claude", plan, False),
            )

            actions = update_install(
                source,
                destination,
                "claude",
                None,
                select_all=False,
                dry_run=False,
                symlink=False,
                replace=False,
            )
            self.assertTrue(any("UPDATE file" in action for action in actions))
            self.assertTrue(manifest_path(destination).is_file())

            actions = uninstall(
                destination,
                ["beta"],
                select_all=False,
                dry_run=False,
                force=False,
            )
            self.assertIn("UNINSTALL file", actions[0])
            self.assertTrue((destination / "alpha").exists())
            self.assertTrue(manifest_path(destination).is_file())

            actions = uninstall(
                destination,
                None,
                select_all=False,
                dry_run=False,
                force=False,
            )
            self.assertIn("UNINSTALL file", actions[0])
            self.assertTrue((destination / "alpha").is_dir())
            self.assertFalse((destination / "alpha" / "SKILL.md").exists())
            self.assertFalse(manifest_path(destination).exists())

    def test_all_flag_installs_every_skill_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = make_source(root)
            destination = root / "destination"
            with redirect_stdout(StringIO()):
                status = main(
                    [
                        "--target",
                        "claude",
                        "--source",
                        str(source),
                        "--destination",
                        str(destination),
                        "--all",
                    ]
                )
            self.assertEqual(status, 0)
            self.assertTrue((destination / "alpha").is_dir())
            self.assertTrue((destination / "beta").is_dir())
            self.assertTrue(manifest_path(destination).is_file())

    def test_update_removes_skill_removed_from_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = make_source(root)
            destination = root / "destination"
            plan = build_plan(source, destination, ["alpha", "beta"])
            execute_plan(plan)
            _write_manifest(
                manifest_path(destination),
                build_manifest(source, destination, "claude", plan, False),
            )
            (source / "skills" / "beta" / "SKILL.md").unlink()
            (source / "skills" / "beta").rmdir()

            actions = update_install(
                source,
                destination,
                "claude",
                None,
                select_all=False,
                dry_run=False,
                symlink=False,
                replace=False,
            )
            self.assertTrue(any("UPDATE file" in action for action in actions))
            self.assertTrue((destination / "beta").is_dir())
            self.assertFalse((destination / "beta" / "SKILL.md").exists())
            self.assertNotIn('"name": "beta"', manifest_path(destination).read_text())

    def test_legacy_manifest_uninstall_preserves_skill_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = make_source(root)
            destination = root / "destination"
            plan = build_plan(source, destination, ["alpha"])
            execute_plan(plan)
            data = build_manifest(source, destination, "claude", plan, False)
            data["schema_version"] = 1
            for entry in data["managed_skills"]:
                entry.pop("files")
            _write_manifest(manifest_path(destination), data)

            uninstall(
                destination,
                None,
                select_all=False,
                dry_run=False,
                force=False,
            )
            self.assertTrue((destination / "alpha").is_dir())
            self.assertFalse((destination / "alpha" / "SKILL.md").exists())
            self.assertFalse(manifest_path(destination).exists())

    def test_manifest_refuses_modified_skill_without_override(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = make_source(root)
            destination = root / "destination"
            plan = build_plan(source, destination, ["alpha"])
            execute_plan(plan)
            _write_manifest(
                manifest_path(destination),
                build_manifest(source, destination, "claude", plan, False),
            )
            (destination / "alpha" / "local-edit.md").write_text(
                "local edit\n",
                encoding="utf-8",
            )

            with self.assertRaises(InstallationError):
                update_install(
                    source,
                    destination,
                    "claude",
                    None,
                    select_all=False,
                    dry_run=False,
                    symlink=False,
                    replace=False,
                )
            with self.assertRaises(InstallationError):
                uninstall(
                    destination,
                    None,
                    select_all=False,
                    dry_run=False,
                    force=False,
                )
            update_install(
                source,
                destination,
                "claude",
                None,
                select_all=False,
                dry_run=False,
                symlink=False,
                replace=True,
            )
            (destination / "alpha" / "another-edit.md").write_text(
                "another edit\n",
                encoding="utf-8",
            )
            uninstall(
                destination,
                None,
                select_all=False,
                dry_run=False,
                force=True,
            )
            self.assertTrue((destination / "alpha").is_dir())
            self.assertTrue((destination / "alpha" / "local-edit.md").is_file())
            self.assertTrue((destination / "alpha" / "another-edit.md").is_file())
            self.assertFalse(manifest_path(destination).exists())

    def test_manifest_refuses_removing_a_required_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = make_source(root)
            for name in ("adversarial-review", "auto-review"):
                skill = source / "skills" / name
                skill.mkdir()
                (skill / "SKILL.md").write_text(
                    f"---\nname: {name}\ndescription: fixture.\n---\n",
                    encoding="utf-8",
                )
            destination = root / "destination"
            plan = build_plan(source, destination, ["auto-review"])
            execute_plan(plan)
            _write_manifest(
                manifest_path(destination),
                build_manifest(source, destination, "claude", plan, False),
            )

            with self.assertRaises(InstallationError):
                uninstall(
                    destination,
                    ["adversarial-review"],
                    select_all=False,
                    dry_run=False,
                    force=False,
                )


if __name__ == "__main__":
    unittest.main()
