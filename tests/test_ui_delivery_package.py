"""GEB-L3
Input: isolated package source fixtures and the UI delivery builder.
Output: reproducibility, portability and rejection tests; no global installation.
Pos: repository packaging regression tests.
"""
import importlib.util
import json
import shutil
from pathlib import Path
import tempfile
import unittest
import zipfile

BUILDER = Path(__file__).resolve().parents[1] / "scripts/build_ui_delivery_plugin.py"


class PackageTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location("ui_package", BUILDER)
        self.builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.builder)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        recipe = self.source / "plugins/ui-delivery/.codex-plugin"
        recipe.mkdir(parents=True)
        (recipe / "plugin.json").write_text(json.dumps({
            "name": "ui-delivery", "version": "0.1.0", "skills": "./skills/"
        }))
        (self.source / "LICENSE").write_text("MIT test fixture\n")
        (recipe.parent / "README.md").write_text("Fixture instructions\n")
        for name in self.builder.SKILLS:
            skill = self.source / "skills" / name
            (skill / "agents").mkdir(parents=True)
            (skill / "SKILL.md").write_text(f"---\nname: {name}\ndescription: fixture\n---\n")
            (skill / "agents/openai.yaml").write_text("interface: {}\n")

    def test_reproducible_self_contained_archive(self):
        first = self.builder.build(self.source, self.root / "one")
        second = self.builder.build(self.source, self.root / "two")
        self.assertEqual(first.read_bytes(), second.read_bytes())
        with zipfile.ZipFile(first) as archive:
            names = archive.namelist()
            for skill in self.builder.SKILLS:
                self.assertIn(f"ui-delivery/skills/{skill}/SKILL.md", names)
            self.assertIn("ui-delivery/LICENSE", names)
            manifest = json.loads(archive.read("ui-delivery/package-lock.json"))
            self.assertEqual(len(manifest["skills"]), 9)
            self.assertTrue(all(len(v) == 64 for v in manifest["files"].values()))
            self.assertTrue(all(not n.startswith("/") and ".." not in n.split("/") for n in names))

    def test_missing_skill_rejected_without_output(self):
        (self.source / "skills/ui-motion-design/SKILL.md").unlink()
        with self.assertRaises(ValueError):
            self.builder.build(self.source, self.root / "out")
        self.assertFalse((self.root / "out").exists())

    def test_symlink_never_copies_outside_content(self):
        (self.source / "skills/ui-delivery/leak.md").symlink_to(self.source / "LICENSE")
        with self.assertRaises(ValueError):
            self.builder.build(self.source, self.root / "out")

    def test_secret_file_rejected(self):
        (self.source / "skills/ui-delivery/.env").write_text("fixture only")
        with self.assertRaises(ValueError):
            self.builder.build(self.source, self.root / "out")

    def test_does_not_overwrite_previous_package(self):
        self.builder.build(self.source, self.root / "out")
        with self.assertRaises(FileExistsError):
            self.builder.build(self.source, self.root / "out")

    def test_rejects_disagreeing_portable_manifest(self):
        (self.source / "plugins/ui-delivery/plugin.json").write_text(json.dumps({
            "name": "ui-delivery", "version": "9.9.9"
        }))
        with self.assertRaises(ValueError):
            self.builder.build(self.source, self.root / "out")

    def test_readme_links_cannot_depend_on_source_repository(self):
        readme = self.source / "plugins/ui-delivery/README.md"
        readme.write_text("[Broken](../../skills/ui-delivery/SKILL.md)\n")
        with self.assertRaises(ValueError):
            self.builder.build(self.source, self.root / "broken")
        readme.write_text("[Entry](./skills/ui-delivery/SKILL.md)\n")
        self.assertTrue(self.builder.build(self.source, self.root / "working").exists())

    def test_rejects_symlinked_recipe_directory(self):
        recipe = self.source / "plugins/ui-delivery"
        external = self.root / "external-recipe"
        shutil.copytree(recipe, external)
        recipe.rename(self.source / "plugins/original-recipe")
        recipe.symlink_to(external, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.builder.build(self.source, self.root / "out")

    def test_rejects_symlinked_skills_parent(self):
        skills = self.source / "skills"
        real = self.source / "original-skills"
        skills.rename(real)
        skills.symlink_to(real, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.builder.build(self.source, self.root / "out")


if __name__ == "__main__":
    unittest.main()
