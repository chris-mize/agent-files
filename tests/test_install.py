from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.install import (
    InstallationError,
    build_plan,
    execute_plan,
    selected_skills,
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


if __name__ == "__main__":
    unittest.main()
