"""Register the pinned upstream Claude skill render in project-local discovery."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil

from team_tools import WORKSPACE, load_lock
from register_gstack import adapt as adapt_runtime, skill_destination, check_skill_output

MARKER = '.project-gstack.json'
GENERATED = '<!-- AUTO-GENERATED from'


def _skill_name(path: Path) -> str:
    text = (path / 'SKILL.md').read_text(encoding='utf-8')
    match = re.match(r'\A---\r?\n(.*?)\r?\n---', text, re.S)
    names = re.findall(r'^name:\s*([^\r\n]+)', match.group(1), re.M) if match else []
    if len(names) != 1 or not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}', names[0]):
        raise ValueError(f'Invalid Claude skill manifest: {path / "SKILL.md"}')
    return names[0]


def _rewrite_paths(text: str, render: Path) -> str:
    for rendered_root in {str(render.resolve()), render.resolve().as_posix()}:
        text = text.replace(rendered_root, '.local_runtime/gstack/render/claude')
    source_prefix = '.local_runtime/tooling/.agents/skills/gstack/'
    for home_prefix in ('~/.claude/skills/gstack/', '$HOME/.claude/skills/gstack/', '${HOME}/.claude/skills/gstack/', '.claude/skills/gstack/'):
        text = text.replace(home_prefix, source_prefix)
    for home_prefix in ('~/.gstack/', '$HOME/.gstack/', '${HOME}/.gstack/'):
        text = text.replace(home_prefix, '.local_runtime/gstack/')
    return text


def _adapt(text: str, name: str, render: Path) -> str:
    if GENERATED not in text:
        raise ValueError(f'Not an upstream generated Claude skill: {name}')
    front = re.match(r'\A---\r?\n.*?\r?\n---', text, re.S)
    if not front:
        raise ValueError(f'Missing Claude skill frontmatter: {name}')
    folder_name = 'gstack' if name == 'gstack' else f'gstack-{name.removeprefix("gstack-")}'
    changed = re.sub(r'^name:.*$', f'name: {folder_name}', front.group(), count=1, flags=re.M)
    text = changed + text[front.end():]
    # Keep lazy section references in the ignored render and point executable
    # helpers at the pinned runtime checkout. Paths are relative to repo root.
    # Reuse the relocatable project preamble, including explicit GSTACK_HOME.
    text = _rewrite_paths(text, render)
    text = text.replace('.local_runtime/tooling/.agents/skills/gstack/', '$GSTACK_ROOT/')
    text = text.replace('.local_runtime/gstack/', '$GSTACK_HOME/')
    return adapt_runtime(text, folder_name, host='claude')


def _render_skills(render: Path) -> list[Path]:
    candidates = [render, *(p for p in render.iterdir() if p.is_dir())]
    skills = [p for p in candidates if (p / 'SKILL.md').is_file()]
    if not skills:
        raise ValueError(f'No Claude skills found in render: {render}')
    names = ['gstack' if _skill_name(p) == 'gstack' else
             f'gstack-{_skill_name(p).removeprefix("gstack-")}' for p in skills]
    if len(names) != len(set(names)):
        raise ValueError('Duplicate names in Claude render')
    return sorted(skills)


def register_claude(root: Path = WORKSPACE, render: Path | None = None) -> int:
    root = root.resolve()
    render = (render or (root / '.local_runtime/gstack/render/claude')).resolve()
    lock = load_lock(root)
    skills = _render_skills(render)
    expected = lock['expected_skills']
    if len(skills) != expected:
        raise ValueError(f'Expected {expected} upstream Claude skills, found {len(skills)}')

    prepared = []
    for folder in skills:
        name = _skill_name(folder)
        target_name = 'gstack' if name == 'gstack' else f'gstack-{name.removeprefix("gstack-")}'
        target = skill_destination(root, 'claude', target_name, lock)
        content = _adapt((folder / 'SKILL.md').read_text(encoding='utf-8'), name, render)
        files = [folder / 'SKILL.md'] if folder == render else [
            p for p in folder.rglob('*') if p.is_file()]
        for file in files:
            check_skill_output(target, file.relative_to(folder))
        check_skill_output(target, Path(MARKER))
        # Refuse a previous leaking install before changing any current skill.
        if target.exists() and any(p.parent != target for p in target.rglob('SKILL.md')):
            raise ValueError(f'Nested/fixture skill in previous installation: {target}; '
                             'run unregister_claude() before reinstalling')
        prepared.append((folder, target, content, files))

    for folder, target, content, files in prepared:
        target.mkdir(parents=True, exist_ok=True)
        for file in files:
            relative = file.relative_to(folder)
            output = target / relative
            output.parent.mkdir(parents=True, exist_ok=True)
            if output.exists() and relative != Path('SKILL.md'):
                existing = output.read_text(encoding='utf-8') if output.suffix == '.md' else ''
                if GENERATED not in existing and not (target / MARKER).is_file():
                    raise ValueError(f'Refusing to overwrite user-owned Claude skill file: {output}')
            if relative == Path('SKILL.md'):
                output.write_text(content, encoding='utf-8', newline='\n')
            elif file.suffix == '.md':
                asset = file.read_text(encoding='utf-8')
                asset = _rewrite_paths(asset, render)
                output.write_text(asset, encoding='utf-8', newline='\n')
            else:
                shutil.copy2(file, output)
        (target / MARKER).write_text(json.dumps({
            'repository': lock['repository'], 'commit': lock['commit'], 'host': 'claude'
        }) + '\n', encoding='utf-8')
    return len(prepared)


def unregister_claude(root: Path = WORKSPACE) -> int:
    """Remove only Claude registrations created by this pinned project installer."""
    root = root.resolve()
    lock = load_lock(root)
    skills_root = (root / '.claude/skills').resolve()
    if skills_root.parent != root / '.claude':
        raise ValueError('Unexpected Claude skills root')
    removed = 0
    if not skills_root.is_dir():
        return removed
    for target in sorted(skills_root.iterdir()):
        if not (target.name == 'gstack' or target.name.startswith('gstack-')) or not target.is_dir():
            continue
        marker_path = target / MARKER
        if not marker_path.is_file():
            continue
        marker = json.loads(marker_path.read_text(encoding='utf-8'))
        if (marker.get('repository') != lock['repository'] or marker.get('commit') != lock['commit']
                or marker.get('host') != 'claude'):
            continue
        resolved = target.resolve()
        if resolved.parent != skills_root:
            raise ValueError(f'Refusing to remove a path outside Claude skills: {target}')
        shutil.rmtree(resolved)
        removed += 1
    return removed


def validate_claude_discovery(root: Path = WORKSPACE) -> int:
    root = root.resolve()
    skills_root = root / '.claude/skills'
    manifests = sorted(p for folder in skills_root.glob('gstack*') if folder.is_dir()
                       for p in folder.rglob('SKILL.md'))
    names = []
    for path in manifests:
        if path.parent.parent != skills_root:
            raise ValueError(f'Nested/fixture Claude skill: {path}')
        name = _skill_name(path.parent)
        if name != path.parent.name:
            raise ValueError(f'Claude skill name differs from its folder: {path}')
        marker = json.loads((path.parent / MARKER).read_text(encoding='utf-8'))
        lock = load_lock(root)
        if marker.get('repository') != lock['repository'] or marker.get('commit') != lock['commit'] or marker.get('host') != 'claude':
            raise ValueError(f'Claude skill does not match the pinned source: {path}')
        names.append(name)
    expected = load_lock(root)['expected_skills']
    if len(names) != expected or len(set(names)) != expected:
        raise ValueError(f'Expected {expected} unique project-local Claude skills, found {len(names)}')
    return len(names)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--render', type=Path)
    args = parser.parse_args()
    if not args.check:
        print(f'Registered {register_claude(render=args.render)} Claude skills')
    print(f'Claude discovery verified: {validate_claude_discovery()} skills')
