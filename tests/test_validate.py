from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate import (
    _validate_marketplace,
    parse_frontmatter,
    validate_repository,
    validate_skill,
)
from scripts.metadata import bundle_version


ROOT = Path(__file__).resolve().parents[1]


class ValidateTests(unittest.TestCase):
    def test_repository_passes(self) -> None:
        self.assertEqual(validate_repository(ROOT), [])

    def test_bundle_version_comes_from_canonical_marketplace_metadata(self) -> None:
        marketplace = json.loads(
            (ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8")
        )
        self.assertEqual(bundle_version(), marketplace["metadata"]["version"])

    def test_invalid_frontmatter_fixture_is_rejected(self) -> None:
        text = (ROOT / "tests/fixtures/invalid-frontmatter.md").read_text(
            encoding="utf-8"
        )
        frontmatter, error = parse_frontmatter(text)
        self.assertIsNone(error)
        self.assertEqual(frontmatter["name"], "Bad Name")
        self.assertEqual(frontmatter["description"], "")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            skill_dir = root / "Bad Name"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(text, encoding="utf-8")
            errors = validate_skill(skill_dir, root)
        self.assertTrue(any("invalid skill name" in error for error in errors))
        self.assertTrue(any("description must be non-empty" in error for error in errors))

    def test_machine_specific_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            skill_dir = root / "fixture"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                (ROOT / "tests/fixtures/machine-path.md").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            errors = validate_skill(skill_dir, root)
        self.assertTrue(any("machine-specific" in error for error in errors))

    def test_missing_relative_link_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            skill_dir = root / "fixture"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                "---\nname: fixture\ndescription: A fixture.\n---\n\n[missing](nope.md)\n",
                encoding="utf-8",
            )
            errors = validate_skill(skill_dir, root)
        self.assertTrue(any("links to missing path" in error for error in errors))

    def test_escaping_relative_link_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            skill_dir = root / "src/skills/fixture"
            skill_dir.mkdir(parents=True)
            (root / "outside.md").write_text("outside\n", encoding="utf-8")
            (skill_dir / "SKILL.md").write_text(
                "---\nname: fixture\ndescription: A fixture.\n---\n\n"
                "[outside](../../outside.md)\n",
                encoding="utf-8",
            )
            errors = validate_skill(skill_dir, root)
        self.assertTrue(any("outside the package skill tree" in error for error in errors))

    def test_codex_marketplace_rejects_noncanonical_owner_field(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / ".agents/plugins/marketplace.json"
            path.parent.mkdir(parents=True)
            data = json.loads(
                (ROOT / ".agents/plugins/marketplace.json").read_text(encoding="utf-8")
            )
            data["owner"] = {"name": "unexpected"}
            path.write_text(json.dumps(data), encoding="utf-8")
            errors: list[str] = []
            _validate_marketplace(path, root, errors)
        self.assertTrue(any("unsupported Codex marketplace keys" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
