"""Behavioral checks for safe skill registration and relocated workspaces."""
from pathlib import Path
import json
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from register_gstack import adapt, register, validate_discovery
from team_tools import SOURCE_RELATIVE, find_git_bash, run

SAMPLE = '''---
name: review
description: Review a change.
---
<!-- AUTO-GENERATED from SKILL.md.tmpl -->
_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
GSTACK_ROOT="$HOME/.codex/skills/gstack"
[ -n "$_ROOT" ] && [ -d "$_ROOT/.agents/skills/gstack" ] && GSTACK_ROOT="$_ROOT/.agents/skills/gstack"
```yaml
name: example-inside-the-body
```
'''

class WindowsToolResolutionTests(unittest.TestCase):
    def make_git_install(self, root, git_relative):
        git = root / git_relative
        bash = root / 'bin/bash.exe'
        for path in (git, bash):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'')
        return git, bash

    def test_git_bash_is_found_from_cmd_and_mingw64_git(self):
        for git_relative in ('cmd/git.exe', 'mingw64/bin/git.exe'):
            with self.subTest(git_relative), tempfile.TemporaryDirectory() as directory:
                git, bash = self.make_git_install(Path(directory), git_relative)
                self.assertEqual(find_git_bash(git), bash.resolve())

    def test_git_without_git_bash_is_not_resolved(self):
        with tempfile.TemporaryDirectory() as directory:
            git = Path(directory) / 'tools/mingw64/bin/git.exe'
            git.parent.mkdir(parents=True)
            git.write_bytes(b'')
            self.assertIsNone(find_git_bash(git))

    def test_run_resolves_bare_tool_from_the_given_path(self):
        completed = mock.Mock(stdout='')
        with mock.patch('team_tools.shutil.which', return_value='C:/npm/bun.CMD') as which,                 mock.patch('team_tools.subprocess.run', return_value=completed) as process:
            run(['bun', 'install'], env={'PATH': 'C:/npm'})
        which.assert_called_once_with('bun', path='C:/npm')
        self.assertEqual(process.call_args.args[0], ['C:/npm/bun.CMD', 'install'])

    def test_run_keeps_unresolved_tool_for_the_process_error(self):
        completed = mock.Mock(stdout='')
        with mock.patch('team_tools.shutil.which', return_value=None),                 mock.patch('team_tools.subprocess.run', return_value=completed) as process:
            run(['missing-tool', '--version'])
        self.assertEqual(process.call_args.args[0], ['missing-tool', '--version'])

class TeamSetupTests(unittest.TestCase):
    def make_workspace(self, root):
        (root / 'tooling').mkdir()
        (root / 'tooling/gstack.lock.json').write_text(json.dumps({
            'commit': 'a' * 40, 'repository': 'https://example.test/gstack.git', 'expected_skills': 1}), encoding='utf-8')
        skill = root / SOURCE_RELATIVE / '.agents/skills/gstack-review'
        skill.mkdir(parents=True)
        (skill / 'SKILL.md').write_text(SAMPLE, encoding='utf-8')
        custom = root / '.agents/skills/jipdam-workflow'
        custom.mkdir(parents=True)
        (custom / 'SKILL.md').write_text('---\nname: jipdam-workflow\ndescription: Project workflow.\n---\n', encoding='utf-8')

    def test_body_name_survives_and_runtime_is_outside_discovery(self):
        output = adapt(SAMPLE, 'gstack-review')
        self.assertIn('name: example-inside-the-body', output)
        self.assertIn('GSTACK_ROOT="$_ROOT/.local_runtime/tooling/', output)
        self.assertNotIn('GSTACK_ROOT="$HOME/.codex/', output)

    def test_foreign_skill_is_preserved_when_registration_refuses(self):
        with tempfile.TemporaryDirectory(prefix='team test ') as temp:
            root = Path(temp)
            self.make_workspace(root)
            foreign = root / '.agents/skills/gstack-review'
            foreign.mkdir()
            original = '---\nname: my-review\ndescription: My own review.\n---\n'
            (foreign / 'SKILL.md').write_text(original, encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'user-owned'):
                register(root)
            self.assertEqual((foreign / 'SKILL.md').read_text(encoding='utf-8'), original)

    def test_relocated_registration_is_repeatable_and_fixture_leak_fails(self):
        with tempfile.TemporaryDirectory(prefix='team test ') as temp:
            root = Path(temp)
            self.make_workspace(root)
            register(root)
            path = root / '.agents/skills/gstack-review/SKILL.md'
            first = path.read_bytes()
            register(root)
            self.assertEqual(first, path.read_bytes())
            self.assertEqual(validate_discovery(root), 2)
            fixture = root / '.agents/skills/gstack-review/test/alpha'
            fixture.mkdir(parents=True)
            (fixture / 'SKILL.md').write_text('---\nname: alpha\ndescription: Fixture.\n---\n', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'Nested/fixture'):
                validate_discovery(root)

if __name__ == '__main__':
    unittest.main()
