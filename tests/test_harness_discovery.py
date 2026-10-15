"""Project-owned roles must coexist with the pinned generated gstack skill set."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from register_gstack import validate_discovery


class HarnessDiscoveryTests(unittest.TestCase):
    def test_project_skill_preserves_pin_and_nested_guards(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "tooling").mkdir()
            # Use the actual pin contract, changing only the fixture skill count.
            lock = json.loads((Path(__file__).resolve().parents[1] / "tooling/gstack.lock.json").read_text(encoding="utf-8"))
            lock["expected_skills"] = 1
            (root / "tooling/gstack.lock.json").write_text(json.dumps(lock), encoding="utf-8")
            for name in ("gstack", "jipdam-workflow", "jipdam-harness"):
                folder = root / ".agents/skills" / name
                folder.mkdir(parents=True)
                (folder / "SKILL.md").write_text(f"---\nname: {name}\ndescription: fixture\n---\n", encoding="utf-8")
            self.assertEqual(validate_discovery(root), 3)
            bad = root / ".agents/skills/gstack/fake/SKILL.md"
            bad.parent.mkdir()
            bad.write_text("---\nname: fake\ndescription: fixture\n---\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Nested/fixture"):
                validate_discovery(root)
            bad.unlink()
            (root / ".agents/skills/gstack/SKILL.md").unlink()
            with self.assertRaisesRegex(ValueError, "Expected 1 gstack"):
                validate_discovery(root)
