from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
import tempfile
import unittest
from pathlib import Path

from scripts.install import main as install_main, manifest_path
from scripts.uninstall import uninstall_main


class UninstallScriptTests(unittest.TestCase):
    def test_script_removes_manifest_files_and_preserves_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "src"
            skill = source / "skills" / "alpha"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: alpha\ndescription: fixture.\n---\n",
                encoding="utf-8",
            )
            destination = root / "destination"

            with redirect_stdout(StringIO()):
                self.assertEqual(
                    install_main(
                        [
                            "--target",
                            "claude",
                            "--source",
                            str(source),
                            "--destination",
                            str(destination),
                            "--all",
                        ]
                    ),
                    0,
                )
            preview = StringIO()
            with redirect_stdout(preview):
                self.assertEqual(
                    uninstall_main(
                        [
                            "--target",
                            "claude",
                            "--destination",
                            str(destination),
                            "--dry-run",
                        ]
                    ),
                    0,
                )
            self.assertIn("DRY-RUN file", preview.getvalue())
            self.assertTrue((destination / "alpha" / "SKILL.md").exists())

            user_file = destination / "alpha" / "user-owned.txt"
            user_file.write_text("keep me\n", encoding="utf-8")
            with redirect_stdout(StringIO()):
                self.assertEqual(
                    uninstall_main(
                        [
                            "--target",
                            "claude",
                            "--destination",
                            str(destination),
                            "--force",
                        ]
                    ),
                    0,
                )
            self.assertTrue((destination / "alpha").is_dir())
            self.assertFalse((destination / "alpha" / "SKILL.md").exists())
            self.assertTrue(user_file.is_file())
            self.assertFalse(manifest_path(destination).exists())


if __name__ == "__main__":
    unittest.main()
