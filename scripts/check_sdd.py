"""Validate registered SDD contracts, evidence and changed-path Task coverage offline."""
from __future__ import annotations

import argparse
import ast
from datetime import date
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tomllib
from urllib.parse import urlsplit

from team_tools import WORKSPACE

REGISTRY = 'docs/sdd/traceability.json'
SPEC_STATES = {'draft', 'approved', 'baseline', 'superseded'}
TASK_STATES = {'draft', 'ready', 'in_progress', 'verified', 'blocked'}
ID = re.compile(r'[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+\Z')


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def strings(value: object, label: str) -> list[str]:
    require(isinstance(value, list) and bool(value) and all(nonempty(x) for x in value),
            f'{label}: expected a nonempty string array')
    require(len(value) == len(set(value)), f'{label}: duplicate entries')
    return value


def relative_path(value: str) -> PurePosixPath:
    require(nonempty(value) and '\\' not in value and ':' not in value and not value.startswith('/'),
            f'Invalid repository path: {value!r}')
    path = PurePosixPath(value)
    require(not any(part in {'..', '.'} for part in value.split('/'))
            and not any(c in value for c in '*?[]') and bool(path.parts),
            f'Invalid repository path: {value!r}')
    return path


def file_path(root: Path, value: str) -> Path:
    path = root / relative_path(value)
    require(path.resolve().is_relative_to(root.resolve()), f'Path escapes repository: {value}')
    require(path.is_file(), f'Missing file: {value}')
    return path


def headings(text: str) -> list[str]:
    return re.findall(r'^#{1,6}\s+(.+?)\s*#*\s*$', text, re.MULTILINE)


def evidence_exists(root: Path, reference: str) -> None:
    require(nonempty(reference), 'Evidence reference must be nonempty')
    if reference.startswith('https://'):
        url = urlsplit(reference)
        require(bool(url.hostname) and not url.username and not url.password,
                f'Invalid evidence URL: {reference}')
        return  # Do not contact external services from model-free CI.
    name, separator, anchor = reference.partition('#')
    path = file_path(root, name)
    if separator:
        anchors = {re.sub(r'[^\w -]', '', h.casefold()).replace(' ', '-')
                   for h in headings(path.read_text(encoding='utf-8'))}
        require(bool(anchor) and anchor in anchors, f'Missing evidence anchor: {reference}')


def metadata(root: Path, name: str, kind: str) -> tuple[dict, str]:
    text = file_path(root, name).read_text(encoding='utf-8')
    match = re.search(r'^```toml\s*\n(.*?)^```\s*$', text, re.MULTILINE | re.DOTALL)
    require(match is not None, f'{name}: missing TOML metadata')
    try:
        meta = tomllib.loads(match.group(1))
    except tomllib.TOMLDecodeError as error:
        raise ValueError(f'{name}: invalid TOML: {error}') from error
    require(meta.get('kind') == kind, f'{name}: expected kind={kind}')
    require(nonempty(meta.get('owner')), f'{name}: missing owner')
    states = SPEC_STATES if kind == 'spec' else TASK_STATES
    require(meta.get('status') in states, f'{name}: invalid {kind} status')
    if kind == 'spec':
        require(type(meta.get('revision')) is int and meta['revision'] > 0,
                f'{name}: revision must be a positive integer')
        if meta['status'] == 'approved':
            for field in ('approved_by', 'approved_at', 'approval_ref'):
                require(nonempty(meta.get(field)), f'{name}: missing {field}')
            try:
                date.fromisoformat(meta['approved_at'])
            except ValueError as error:
                raise ValueError(f'{name}: approved_at must be an ISO date') from error
    return meta, text


def test_exists(root: Path, test: dict, cache: dict) -> None:
    require(isinstance(test, dict), 'Test reference must be an object')
    name, class_name, method = (test.get(key) for key in ('file', 'class', 'method'))
    require(all(nonempty(x) for x in (name, class_name, method)), 'Incomplete test reference')
    path = file_path(root, name)
    require(path.suffix == '.py' and method.startswith('test_'), f'Invalid unittest reference: {test}')
    if name not in cache:
        try:
            cache[name] = ast.parse(path.read_text(encoding='utf-8'), filename=name)
        except SyntaxError as error:
            raise ValueError(f'{name}: test source has a syntax error') from error
    classes = [node for node in cache[name].body if isinstance(node, ast.ClassDef) and node.name == class_name]
    require(len(classes) == 1, f'Missing/duplicate test class: {name}:{class_name}')
    cls = classes[0]
    require(any(isinstance(base, ast.Attribute) and base.attr == 'TestCase'
                or isinstance(base, ast.Name) and base.id == 'TestCase' for base in cls.bases),
            f'Test class must directly inherit unittest.TestCase: {name}:{class_name}')
    methods = [node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == method]
    require(len(methods) == 1, f'Missing/duplicate test method: {name}:{class_name}.{method}')
    decorators = [d.func if isinstance(d, ast.Call) else d
                  for d in [*cls.decorator_list, *methods[0].decorator_list]]
    decorator_names = [d.attr if isinstance(d, ast.Attribute) else d.id if isinstance(d, ast.Name) else ''
                       for d in decorators]
    require(not any(name.startswith('skip') or name == 'expectedFailure' for name in decorator_names),
            f'Skipped test cannot supply AC evidence: {name}:{class_name}.{method}')


def explanatory_document(name: str) -> bool:
    path = relative_path(name)
    forbidden = {'specs', 'adr', 'tasks', 'templates', 'plans', 'sdd', '.agents', '.codex', '.github'}
    if any(part.casefold() in forbidden for part in path.parts):
        return False
    if path.name.casefold() in {'agents.md', 'claude.md', 'gemini.md', 'sdd.md'} or path.name.endswith('_spec.md'):
        return False
    return path.name == 'README.md' or path.suffix == '.md' and path.parts[0] == 'docs'


def scope_covers(scope: str, name: str) -> bool:
    relative_path(scope)
    return name.startswith(scope) if scope.endswith('/') else name == scope


def validate(root: Path, changed_paths: list[str] | None = None) -> dict:
    try:
        data = json.loads(file_path(root, REGISTRY).read_text(encoding='utf-8'))
    except json.JSONDecodeError as error:
        raise ValueError(f'{REGISTRY}: invalid JSON') from error
    require(isinstance(data, dict) and type(data.get('schema_version')) is int
            and data['schema_version'] == 1, 'Unsupported SDD schema_version')
    features = data.get('features')
    require(isinstance(features, list) and bool(features), 'Missing features')
    ids: set[str] = set()
    ac_specs: dict[str, str] = {}
    spec_states: dict[str, str] = {}
    test_cache: dict = {}

    def register_id(value: str) -> None:
        require(nonempty(value) and ID.fullmatch(value) is not None, f'Invalid ID: {value!r}')
        require(value not in ids, f'Duplicate ID: {value}')
        ids.add(value)

    for feature in features:
        require(isinstance(feature, dict), 'Feature must be an object')
        feature_id, spec_name = feature.get('id'), feature.get('spec')
        register_id(feature_id)
        meta, text = metadata(root, spec_name, 'spec')
        require(meta.get('id') == feature_id, f'{spec_name}: feature ID mismatch')
        require(spec_name not in spec_states, f'Duplicate Spec path: {spec_name}')
        spec_states[spec_name] = meta['status']
        declared = re.findall(r'^#{1,6}\s+(' + re.escape(feature_id) + r'-(?:REQ|AC)-[A-Z0-9-]+)\b', text, re.MULTILINE)
        require(len(declared) == len(set(declared)), f'{spec_name}: duplicate requirement/AC heading')
        expected: set[str] = set()
        requirements = feature.get('requirements')
        require(isinstance(requirements, list) and bool(requirements), f'{feature_id}: missing requirements')
        for requirement in requirements:
            require(isinstance(requirement, dict), f'{feature_id}: invalid requirement')
            req_id = requirement.get('id')
            register_id(req_id)
            require(req_id.startswith(feature_id + '-REQ-'), f'{req_id}: wrong requirement prefix')
            expected.add(req_id)
            acs = requirement.get('acs')
            require(isinstance(acs, list) and bool(acs), f'{req_id}: missing ACs')
            for ac in acs:
                require(isinstance(ac, dict), f'{req_id}: invalid AC')
                ac_id = ac.get('id')
                register_id(ac_id)
                require(ac_id.startswith(feature_id + '-AC-'), f'{ac_id}: wrong AC prefix')
                expected.add(ac_id)
                ac_specs[ac_id] = spec_name
                tests, manual = ac.get('tests', []), ac.get('manual', [])
                require(isinstance(tests, list) and isinstance(manual, list) and bool(tests or manual),
                        f'{ac_id}: missing verification mapping')
                for test in tests:
                    test_exists(root, test, test_cache)
                for check in manual:
                    require(isinstance(check, dict) and nonempty(check.get('command')),
                            f'{ac_id}: missing manual command')
                    evidence_exists(root, check.get('evidence'))
        require(set(declared) == expected, f'{spec_name}: requirement/AC headings and registry differ')

    task_names = strings(data.get('tasks'), 'tasks')
    tasks = []
    for name in task_names:
        meta, text = metadata(root, name, 'task')
        task_id = meta.get('id')
        register_id(task_id)
        require(task_id.startswith('TASK-'), f'{name}: wrong Task ID prefix')
        specs = strings(meta.get('specs'), f'{name}: specs')
        for spec in specs:
            file_path(root, spec)
            if meta['status'] in {'ready', 'in_progress', 'verified'} and spec in spec_states:
                require(spec_states[spec] in {'approved', 'baseline'}, f'{name}: Spec not ready: {spec}')
        scope = strings(meta.get('scope'), f'{name}: scope')
        for item in scope:
            relative_path(item)
            require((root / item).resolve().is_relative_to(root.resolve()), f'{name}: scope escapes repository')
        acs = strings(meta.get('acs'), f'{name}: acs')
        for ac_id in acs:
            require(ac_id in ac_specs, f'{name}: unknown AC {ac_id}')
            require(ac_specs[ac_id] in specs, f'{name}: AC Spec not included: {ac_id}')
        records = meta.get('verification', [])
        require(isinstance(records, list), f'{name}: invalid verification records')
        covered: set[str] = set()
        for record in records:
            require(isinstance(record, dict) and nonempty(record.get('command')),
                    f'{name}: missing verification command')
            require(record.get('result') in {'passed', 'failed', 'not_run'}, f'{name}: invalid verification result')
            evidence_exists(root, record.get('evidence'))
            record_acs = strings(record.get('acs'), f'{name}: verification acs')
            require(set(record_acs).issubset(acs), f'{name}: verification includes undeclared AC')
            if record['result'] == 'passed':
                covered.update(record_acs)
        if meta['status'] == 'verified':
            require(set(acs).issubset(covered), f'{name}: verified Task lacks passed evidence for every AC')
            for ac_id in acs:
                require(re.search(r'^- \[[xX]\]\s+' + re.escape(ac_id) + r'(?:\s|$)', text, re.MULTILINE) is not None,
                        f'{name}: verified Task has unchecked AC {ac_id}')
        if meta['status'] == 'blocked':
            require(nonempty(meta.get('blocked_reason')), f'{name}: missing blocked_reason')
        tasks.append((name, meta))

    changed = set(changed_paths or [])
    for name in changed:
        relative_path(name)
    active = [(name, meta) for name, meta in tasks if name in changed
              and meta['status'] in {'ready', 'in_progress', 'verified'}]
    for name in sorted(changed):
        if explanatory_document(name):
            continue
        if 'specs' in PurePosixPath(name).parts or 'tasks' in PurePosixPath(name).parts:
            path = root / name
            if path.is_file() and path.suffix == '.md':
                block = re.search(r'^```toml\s*\n(.*?)^```\s*$', path.read_text(encoding='utf-8'),
                                  re.MULTILINE | re.DOTALL)
                if block:
                    document_meta = tomllib.loads(block.group(1))
                    if document_meta.get('kind') == 'spec':
                        require(name in spec_states, f'{name}: Spec metadata is not registered')
                    elif document_meta.get('kind') == 'task':
                        require(name in task_names, f'{name}: Task metadata is not registered')
        require(any(any(scope_covers(scope, name) for scope in meta['scope']) for _, meta in active),
                f'{name}: no updated ready/in_progress/verified Task covers this change')
    return {'features': len(features), 'acceptance_criteria': len(ac_specs), 'tasks': len(tasks),
            'changed_paths': len(changed), 'status': 'passed'}


def git_output(root: Path, *args: str) -> str:
    result = subprocess.run(['git', '-c', f'safe.directory={root.resolve().as_posix()}',
                             '-c', 'core.excludesFile=', *args], cwd=root, check=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
    return result.stdout


def changed_files(root: Path, base: str | None = None, event: dict | None = None) -> list[str]:
    paths: set[str] = set()
    if event is not None:
        if 'pull_request' in event:
            pull = event['pull_request']
            require(all(re.fullmatch(r'[0-9a-f]{40}', sha) for sha in
                        (pull['base']['sha'], pull['head']['sha'])), 'Invalid CI commit SHA')
            comparison = f"{pull['base']['sha']}...{pull['head']['sha']}"
        else:
            before, after = event.get('before'), event.get('after')
            require(nonempty(before) and nonempty(after), 'CI event must contain push or pull_request SHAs')
            require(re.fullmatch(r'[0-9a-f]{40}', before) is not None
                    and re.fullmatch(r'[0-9a-f]{40}', after) is not None, 'Invalid CI commit SHA')
            if set(after) == {'0'}:
                return []
            if set(before) == {'0'}:
                # A new branch has no before SHA; use the repository's fetched default branch.
                default = event.get('repository', {}).get('default_branch', 'main')
                require(re.fullmatch(r'[A-Za-z0-9_./-]+', default) is not None and not default.startswith('-'),
                        'Invalid default branch')
                comparison = f'origin/{default}...{after}'
            else:
                comparison = f'{before}..{after}'
        paths.update(git_output(root, 'diff', '--name-only', '--no-renames', '-z', comparison, '--').split('\0'))
    elif base:
        require(not base.startswith('-'), 'Invalid base reference')
        paths.update(git_output(root, 'diff', '--name-only', '--no-renames', '-z', f'{base}...HEAD', '--').split('\0'))
    paths.update(git_output(root, 'diff', '--name-only', '--no-renames', '-z', 'HEAD', '--').split('\0'))
    paths.update(git_output(root, 'ls-files', '--others', '--exclude-standard', '-z').split('\0'))
    return sorted(paths - {''})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', help='Compare this branch with a locally available base ref, plus working changes')
    parser.add_argument('--ci', action='store_true', help='Read GitHub event SHAs; never query the network')
    args = parser.parse_args()
    require(not (args.base and args.ci), '--base and --ci are mutually exclusive')
    event = None
    if args.ci:
        event_file = os.environ.get('GITHUB_EVENT_PATH')
        require(nonempty(event_file), '--ci requires GITHUB_EVENT_PATH')
        event = json.loads(Path(event_file).read_text(encoding='utf-8'))
    print(json.dumps(validate(WORKSPACE, changed_files(WORKSPACE, args.base, event)), ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError, subprocess.CalledProcessError) as error:
        print(f'SDD validation failed: {error}', file=sys.stderr)
        sys.exit(1)
