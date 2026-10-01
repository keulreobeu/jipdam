"""Regressions for SDD references, evidence and actual Git change coverage."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from check_sdd import changed_files, git_output, validate


class SDDContractTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.spec = {'kind': 'spec', 'id': 'DEMO-001', 'status': 'baseline', 'owner': 'tester', 'revision': 1}
        self.task = {'kind': 'task', 'id': 'TASK-DEMO-001', 'status': 'ready', 'owner': 'tester',
                     'specs': ['docs/specs/demo.md'], 'scope': ['src/', 'docs/'], 'acs': ['DEMO-001-AC-01']}
        self.registry = {'schema_version': 1, 'features': [{'id': 'DEMO-001', 'spec': 'docs/specs/demo.md',
            'requirements': [{'id': 'DEMO-001-REQ-01', 'acs': [{'id': 'DEMO-001-AC-01', 'tests': [
                {'file': 'tests/test_demo.py', 'class': 'DemoTests', 'method': 'test_contract'}]}]}]}],
            'tasks': ['docs/tasks/demo.md']}
        self.write('tests/test_demo.py', 'import unittest\nclass DemoTests(unittest.TestCase):\n'
                   '    def test_contract(self):\n        self.assertTrue(True)\n')
        self.write('src/demo.py', 'value = 1\n')
        self.write('docs/evidence.md', '# Evidence\n\n## Result\n\nPassed in a synthetic fixture.\n')
        self.write_spec(self.spec)
        self.write_task(self.task)
        self.write_registry(self.registry)

    def write(self, name, text):
        target = self.root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8')

    def block(self, meta):
        base = '\n'.join(f'{key} = {json.dumps(value, ensure_ascii=False)}'
                         for key, value in meta.items() if key != 'verification')
        for record in meta.get('verification', []):
            base += '\n\n[[verification]]\n' + '\n'.join(
                f'{key} = {json.dumps(value, ensure_ascii=False)}' for key, value in record.items())
        return f'```toml\n{base}\n```\n'

    def write_spec(self, meta):
        self.write('docs/specs/demo.md', '# Demo\n' + self.block(meta)
                   + '\n## DEMO-001-REQ-01 Required behavior\n\n### DEMO-001-AC-01 Observable result\n')

    def write_task(self, meta, checked=False):
        self.write('docs/tasks/demo.md', '# Task\n' + self.block(meta)
                   + f'\n- [{"x" if checked else " "}] DEMO-001-AC-01 Result\n')

    def write_registry(self, registry):
        self.write('docs/sdd/traceability.json', json.dumps(registry))

    def test_valid_baseline_and_approved_contracts(self):
        self.assertEqual(validate(self.root)['acceptance_criteria'], 1)
        meta = {**self.spec, 'status': 'approved', 'approved_by': 'user', 'approved_at': '2026-10-01',
                'approval_ref': 'Explicit feature request'}
        self.write_spec(meta)
        self.assertEqual(validate(self.root)['status'], 'passed')

    def test_duplicate_ids_and_invalid_metadata_are_rejected(self):
        registry = deepcopy(self.registry)
        registry['features'][0]['requirements'][0]['acs'][0]['id'] = 'DEMO-001'
        self.write_registry(registry)
        with self.assertRaisesRegex(ValueError, 'Duplicate ID'):
            validate(self.root)
        self.write_registry(self.registry)
        for update in ({'status': 'complete'}, {'owner': ''}, {'revision': True},
                       {'status': 'approved'}, {'status': 'approved', 'approved_by': 'user',
                        'approved_at': 'yesterday', 'approval_ref': 'request'}):
            with self.subTest(update=update):
                self.write_spec({**self.spec, **update})
                with self.assertRaises(ValueError):
                    validate(self.root)
        self.write_spec(self.spec)
        self.write_task({**self.task, 'status': 'blocked'})
        with self.assertRaisesRegex(ValueError, 'blocked_reason'):
            validate(self.root)

    def test_broken_references_are_rejected(self):
        for field, bad in [('spec', 'docs/missing.md'), ('requirement', 'DEMO-001-REQ-99'),
                           ('class', 'MissingTests'), ('method', 'test_missing')]:
            registry = deepcopy(self.registry)
            feature = registry['features'][0]
            if field == 'spec':
                feature['spec'] = bad
            elif field == 'requirement':
                feature['requirements'][0]['id'] = bad
            else:
                feature['requirements'][0]['acs'][0]['tests'][0][field] = bad
            with self.subTest(field=field):
                self.write_registry(registry)
                with self.assertRaises(ValueError):
                    validate(self.root)
        self.write_registry(self.registry)
        self.write_task({**self.task, 'acs': ['DEMO-001-AC-99']})
        with self.assertRaisesRegex(ValueError, 'unknown AC'):
            validate(self.root)

    def test_unmapped_and_skipped_tests_are_rejected(self):
        registry = deepcopy(self.registry)
        registry['features'][0]['requirements'][0]['acs'][0]['tests'] = []
        self.write_registry(registry)
        with self.assertRaisesRegex(ValueError, 'missing verification mapping'):
            validate(self.root)
        self.write_registry(self.registry)
        self.write('tests/test_demo.py', 'import unittest\nclass DemoTests(unittest.TestCase):\n'
                   '    @unittest.skip("no evidence")\n    def test_contract(self):\n        pass\n')
        with self.assertRaisesRegex(ValueError, 'Skipped test'):
            validate(self.root)

    def test_unsafe_paths_are_rejected(self):
        for name in ('../outside.py', '/tmp/outside.py', 'C:/outside.py', 'tests/*.py', 'tests\\test_demo.py'):
            with self.subTest(path=name):
                registry = deepcopy(self.registry)
                registry['features'][0]['requirements'][0]['acs'][0]['tests'][0]['file'] = name
                self.write_registry(registry)
                with self.assertRaisesRegex(ValueError, 'Invalid repository path'):
                    validate(self.root)

    def test_test_references_must_be_discovered_by_default_ci(self):
        source = (self.root / 'tests/test_demo.py').read_text(encoding='utf-8')
        for name in ('docs/helper.py', 'tests/contract_checks.py', 'tests/nested/test_demo.py'):
            with self.subTest(path=name):
                self.write(name, source)
                registry = deepcopy(self.registry)
                registry['features'][0]['requirements'][0]['acs'][0]['tests'][0]['file'] = name
                self.write_registry(registry)
                with self.assertRaisesRegex(ValueError, 'not discovered'):
                    validate(self.root)
        self.write('tests/nested/__init__.py', '')
        self.assertEqual(validate(self.root)['status'], 'passed')

    def test_changed_paths_cannot_escape_repository(self):
        from unittest.mock import patch
        resolve = Path.resolve
        def fake_resolve(path, *args, **kwargs):
            if path == self.root / 'README.md':
                return self.root.parent / 'outside.md'
            return resolve(path, *args, **kwargs)
        with patch.object(Path, 'resolve', fake_resolve):
            with self.assertRaisesRegex(ValueError, 'escapes repository'):
                validate(self.root, ['README.md'])

    def test_unapproved_spec_cannot_start_implementation(self):
        self.write_spec({**self.spec, 'status': 'draft'})
        with self.assertRaisesRegex(ValueError, 'Spec not ready'):
            validate(self.root)
        self.write_task({**self.task, 'status': 'draft'})
        self.assertEqual(validate(self.root)['status'], 'passed')
        self.write_spec({**self.spec, 'status': 'superseded'})
        self.write_task(self.task)
        with self.assertRaisesRegex(ValueError, 'Spec not ready'):
            validate(self.root)

    def test_new_metadata_documents_must_be_registered(self):
        for kind, name, meta in [('spec', 'docs/specs/new.md', self.spec),
                                 ('task', 'docs/tasks/new.md', self.task)]:
            with self.subTest(kind=kind):
                self.write(name, '# New\n' + self.block(meta))
                with self.assertRaisesRegex(ValueError, 'not registered'):
                    validate(self.root, [name, 'docs/tasks/demo.md'])

    def test_changed_code_requires_updated_task(self):
        with self.assertRaisesRegex(ValueError, 'no updated'):
            validate(self.root, ['src/demo.py'])
        self.assertEqual(validate(self.root, ['src/demo.py', 'docs/tasks/demo.md'])['changed_paths'], 2)

    def test_scope_and_task_state_are_enforced(self):
        self.write_task({**self.task, 'scope': ['docs/']})
        with self.assertRaisesRegex(ValueError, 'src/demo.py: no updated'):
            validate(self.root, ['src/demo.py', 'docs/tasks/demo.md'])
        self.write_task({**self.task, 'status': 'draft'})
        with self.assertRaisesRegex(ValueError, 'no updated'):
            validate(self.root, ['src/demo.py', 'docs/tasks/demo.md'])

    def test_explanatory_docs_are_exempt_but_contracts_are_not(self):
        self.assertEqual(validate(self.root, ['README.md', 'docs/guide.md'])['status'], 'passed')
        for name in ('AGENTS.md', 'CLAUDE.md', 'docs/sdd.md', 'docs/templates/task.md',
                     'docs/specs/new.md', 'docs/feature_spec.md', '.agents/skills/demo/SKILL.md',
                     '.github/workflows/verify.yml'):
            with self.subTest(path=name):
                with self.assertRaisesRegex(ValueError, 'no updated'):
                    validate(self.root, [name])

    def test_verified_tasks_require_completed_acs_and_passed_evidence(self):
        verified = {**self.task, 'status': 'verified'}
        self.write_task(verified, checked=True)
        with self.assertRaisesRegex(ValueError, 'lacks passed evidence'):
            validate(self.root)
        record = {'command': 'python -m unittest', 'result': 'failed',
                  'evidence': 'docs/evidence.md#result', 'acs': self.task['acs']}
        self.write_task({**verified, 'verification': [record]}, checked=True)
        with self.assertRaisesRegex(ValueError, 'lacks passed evidence'):
            validate(self.root)
        record['result'] = 'passed'
        for field in ('command', 'evidence', 'acs'):
            with self.subTest(field=field):
                incomplete = {key: value for key, value in record.items() if key != field}
                self.write_task({**verified, 'verification': [incomplete]}, checked=True)
                with self.assertRaises(ValueError):
                    validate(self.root)
        self.write_task({**verified, 'verification': [record]})
        with self.assertRaisesRegex(ValueError, 'unchecked AC'):
            validate(self.root)
        self.write_task({**verified, 'verification': [record]}, checked=True)
        self.assertEqual(validate(self.root)['status'], 'passed')
        self.write_task({**verified, 'verification': [record, {**record, 'result': 'failed'}]}, checked=True)
        with self.assertRaisesRegex(ValueError, 'lacks passed evidence'):
            validate(self.root)

    def test_evidence_anchors_and_manual_checks_are_validated(self):
        registry = deepcopy(self.registry)
        ac = registry['features'][0]['requirements'][0]['acs'][0]
        ac['tests'] = []
        ac['manual'] = [{'command': 'inspect approved setting', 'evidence': 'docs/evidence.md#result'}]
        self.write_registry(registry)
        self.assertEqual(validate(self.root)['status'], 'passed')
        ac['manual'][0]['evidence'] = 'docs/evidence.md#missing'
        self.write_registry(registry)
        with self.assertRaisesRegex(ValueError, 'Missing evidence anchor'):
            validate(self.root)

    def test_changed_files_handle_pr_push_and_renames(self):
        git_output(self.root, 'init', '-b', 'main')
        git_output(self.root, 'add', '.')
        git_output(self.root, '-c', 'user.name=SDD Fixture', '-c', 'user.email=sdd@example.invalid',
                   'commit', '-m', 'baseline')
        before = git_output(self.root, 'rev-parse', 'HEAD').strip()
        git_output(self.root, 'update-ref', 'refs/remotes/origin/main', before)
        (self.root / 'src/demo.py').rename(self.root / 'src/renamed.py')
        self.write_task({**self.task, 'status': 'in_progress'})
        git_output(self.root, 'add', '.')
        git_output(self.root, '-c', 'user.name=SDD Fixture', '-c', 'user.email=sdd@example.invalid',
                   'commit', '-m', 'rename with task')
        after = git_output(self.root, 'rev-parse', 'HEAD').strip()
        expected = ['docs/tasks/demo.md', 'src/demo.py', 'src/renamed.py']
        events = [
            {'before': before, 'after': after},
            {'pull_request': {'base': {'sha': before}, 'head': {'sha': after}}},
            {'before': '0' * 40, 'after': after, 'repository': {'default_branch': 'main'}},
        ]
        for event in events:
            with self.subTest(event=event):
                self.assertEqual(changed_files(self.root, event=event), expected)
                self.assertEqual(validate(self.root, expected)['status'], 'passed')
        self.write('src/untracked.py', 'value = 2\n')
        self.assertEqual(changed_files(self.root, base=before), sorted([*expected, 'src/untracked.py']))
