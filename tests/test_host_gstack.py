"""Registration, host switching and user-owned filesystem boundaries."""
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from register_claude_gstack import _adapt, register_claude, unregister_claude, validate_claude_discovery
from register_gstack import register, unregister, validate_discovery
from team_tools import SOURCE_RELATIVE, bash_executable

def manifest(name):
    return f'''---
name: {name}
description: Test skill.
---
<!-- AUTO-GENERATED from SKILL.md.tmpl -->
_SS="$HOME/.claude/skills/gstack/bin/gstack-skill-start"
[ -x "$_SS" ] || _SS=".claude/skills/gstack/bin/gstack-skill-start"
'''

class HostGstackTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='host setup ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        (self.root / 'tooling').mkdir()
        self.lock = {'commit': 'a' * 40, 'repository': 'https://example.test/gstack', 'expected_skills': 2}
        (self.root / 'tooling/gstack.lock.json').write_text(json.dumps(self.lock), encoding='utf-8')
        self.render = self.root / '.local_runtime/gstack/render/claude'
        for name, folder in [('gstack', self.render), ('review', self.render / 'review')]:
            folder.mkdir(parents=True, exist_ok=True)
            (folder / 'SKILL.md').write_text(manifest(name), encoding='utf-8')
            codex = self.root / SOURCE_RELATIVE / '.agents/skills' / ('gstack' if name == 'gstack' else 'gstack-review')
            codex.mkdir(parents=True)
            (codex / 'SKILL.md').write_text(manifest(name), encoding='utf-8')

    def test_host_switch_keeps_only_selected_manifests_and_custom_skills(self):
        custom = self.root / '.agents/skills/jipdam-workflow'
        custom.mkdir(parents=True)
        (custom / 'SKILL.md').write_text('---\nname: jipdam-workflow\ndescription: Mine.\n---\n', encoding='utf-8')
        register(self.root)
        register_claude(self.root)
        self.assertEqual(unregister(self.root), 2)
        self.assertEqual(validate_claude_discovery(self.root), 2)
        manifests = list((self.root / '.claude/skills').rglob('SKILL.md'))
        self.assertEqual(len(manifests), 2)
        first = {p.relative_to(self.root): p.read_bytes() for p in manifests}
        register_claude(self.root)
        self.assertEqual(first, {p.relative_to(self.root): p.read_bytes() for p in manifests})
        register(self.root)
        self.assertEqual(unregister_claude(self.root), 2)
        self.assertEqual(validate_discovery(self.root), 3)
        self.assertTrue((custom / 'SKILL.md').is_file())

    def test_generated_banner_without_marker_is_still_user_owned(self):
        for host, install in [('.claude', register_claude), ('.agents', register)]:
            with self.subTest(host=host):
                folder = self.root / host / 'skills/gstack-review'
                folder.mkdir(parents=True, exist_ok=True)
                original = manifest('mine')
                (folder / 'SKILL.md').write_text(original, encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'user-owned'):
                    install(self.root)
                self.assertEqual((folder / 'SKILL.md').read_text(encoding='utf-8'), original)
                self.assertFalse((self.root / host / 'skills/gstack').exists())

    def test_foreign_marker_does_not_authorize_overwrite_or_deletion(self):
        for host, install, remove in [('.claude', register_claude, unregister_claude), ('.agents', register, unregister)]:
            with self.subTest(host=host):
                folder = self.root / host / 'skills/gstack-review'
                folder.mkdir(parents=True, exist_ok=True)
                (folder / 'SKILL.md').write_text(manifest('mine'), encoding='utf-8')
                (folder / '.project-gstack.json').write_text(json.dumps({**self.lock, 'commit': 'b' * 40, 'host': 'claude'}), encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'user-owned'):
                    install(self.root)
                self.assertEqual(remove(self.root), 0)
                self.assertTrue((folder / 'SKILL.md').is_file())

    def test_nested_manifest_is_rejected_in_existing_install(self):
        register_claude(self.root)
        nested = self.root / '.claude/skills/gstack/review/SKILL.md'
        nested.parent.mkdir()
        nested.write_text(manifest('review'), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Nested/fixture'):
            validate_claude_discovery(self.root)
        with self.assertRaisesRegex(ValueError, 'Nested/fixture'):
            register_claude(self.root)
        self.assertEqual(unregister_claude(self.root), 2)
        register_claude(self.root)
        self.assertEqual(validate_claude_discovery(self.root), 2)

    def test_claude_helpers_export_relocatable_project_state(self):
        register_claude(self.root)
        text = (self.root / '.claude/skills/gstack-review/SKILL.md').read_text(encoding='utf-8')
        self.assertIn('export GSTACK_HOME=', text)
        self.assertIn('_SS="$GSTACK_ROOT/bin/gstack-skill-start"', text)
        self.assertNotIn('$HOME/.claude', text)
        self.assertNotIn('.claude/skills/gstack/bin', text)
        nested = self.root / 'some/nested/directory'
        nested.mkdir(parents=True)
        preamble = text.split('```bash\n', 1)[1].split('```', 1)[0]
        command = 'export PATH="/usr/bin:/bin:$PATH"\n' + preamble + '\nprintf "%s\\n" "$GSTACK_HOME" "$GSTACK_PLAN_DIR" "$BROWSE_STATE_FILE" "$PLAYWRIGHT_BROWSERS_PATH"'
        result = subprocess.run([bash_executable(), '--noprofile', '--norc', '-c', command],
                                cwd=nested, capture_output=True, text=True, check=True)
        paths = result.stdout.strip().splitlines()
        self.assertTrue(paths[0].endswith(self.root.name + '/.local_runtime/gstack'))
        self.assertEqual(paths[1], paths[0] + '/plans')
        self.assertEqual(paths[2], paths[0] + '/browser/browse.json')
        self.assertEqual(paths[3], paths[0].removesuffix('/gstack') + '/playwright')
        upgrade = _adapt(manifest('upgrade'), 'gstack-upgrade', self.render)
        self.assertIn('bootstrap.py --host claude', upgrade)
        self.assertNotIn('bootstrap.py --host codex', upgrade)

    def test_normalized_duplicate_names_are_rejected_before_writes(self):
        (self.render / 'gstack-review').mkdir()
        (self.render / 'gstack-review/SKILL.md').write_text(manifest('gstack-review'), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            register_claude(self.root)
        self.assertFalse((self.root / '.claude').exists())

    def _junction(self, link, target):
        link.parent.mkdir(parents=True, exist_ok=True)
        if os.name == 'nt':
            result = subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(target)], capture_output=True)
            if result.returncode:
                self.skipTest('Directory junction creation unavailable')
        else:
            link.symlink_to(target, target_is_directory=True)
        # Remove the link before TemporaryDirectory recursively cleans fixtures.
        self.addCleanup(lambda: os.rmdir(link) if os.name == 'nt' else link.unlink())

    def test_redirected_skill_directory_preserves_external_files(self):
        outside = self.root / 'outside'
        outside.mkdir()
        original = manifest('mine')
        (outside / 'SKILL.md').write_text(original, encoding='utf-8')
        for host, install in [('.claude', register_claude), ('.agents', register)]:
            with self.subTest(host=host):
                self._junction(self.root / host / 'skills/gstack-review', outside)
                with self.assertRaisesRegex(ValueError, 'redirected'):
                    install(self.root)
                self.assertEqual((outside / 'SKILL.md').read_text(encoding='utf-8'), original)

    def test_redirected_asset_directory_is_refused_before_any_write(self):
        register_claude(self.root)
        outside = self.root / 'outside'
        outside.mkdir()
        (outside / 'note.md').write_text('preserve', encoding='utf-8')
        (self.render / 'review/assets').mkdir()
        (self.render / 'review/assets/note.md').write_text('replacement', encoding='utf-8')
        self._junction(self.root / '.claude/skills/gstack-review/assets', outside)
        with self.assertRaisesRegex(ValueError, 'redirected'):
            register_claude(self.root)
        self.assertEqual((outside / 'note.md').read_text(encoding='utf-8'), 'preserve')

if __name__ == '__main__':
    unittest.main()
