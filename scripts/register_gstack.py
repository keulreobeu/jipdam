"""Register only Codex skills; keep upstream source and fixtures outside discovery."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import shutil
from team_tools import WORKSPACE, SOURCE_RELATIVE, load_lock

MARKER = '.project-gstack.json'
GENERATED = '<!-- AUTO-GENERATED from'

def manifest_fields(text: str) -> tuple[str, str]:
    match = re.match(r'\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)', text, re.S)
    if not match:
        raise ValueError('Missing YAML frontmatter')
    header = match.group(1)
    names = re.findall(r'^name:\s*([^\r\n]+)', header, re.M)
    if len(names) != 1 or not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}', names[0]):
        raise ValueError('Invalid or duplicate skill name')
    description = re.search(r'^description:\s*([^\r\n]*)(.*)', header, re.M | re.S)
    if not description:
        raise ValueError('Missing skill description')
    scalar, tail = description.groups()
    value = scalar.strip()
    if value in ('|', '>', '|-', '>-'):
        lines = []
        for line in tail.splitlines():
            if line and not line.startswith((' ', '\t')):
                break
            lines.append(line.strip())
        value = '\n'.join(lines).strip()
    if not value or len(value) > 1024:
        raise ValueError('Skill description must contain 1..1024 characters')
    return names[0], value

def adapt(text: str, name: str) -> str:
    front = re.match(r'\A---\r?\n.*?\r?\n---', text, re.S)
    if not front:
        raise ValueError('Generated skill has no frontmatter')
    named = re.sub(r'^name:.*$', 'name: ' + name, front.group(), count=1, flags=re.M)
    text = named + text[front.end():]
    root_block = '''_ROOT="$(pwd -P)"
while [ ! -f "$_ROOT/tooling/gstack.lock.json" ] && [ "$_ROOT" != / ]; do
  _ROOT="$(dirname "$_ROOT")"
done
if [ -f "$_ROOT/tooling/gstack.lock.json" ]; then
  GSTACK_ROOT="$_ROOT/.local_runtime/tooling/.agents/skills/gstack"
  export GSTACK_HOME="$_ROOT/.local_runtime/gstack"
  export GSTACK_PLAN_DIR="$_ROOT/.local_runtime/gstack/plans"
  export PLAYWRIGHT_BROWSERS_PATH="$_ROOT/.local_runtime/playwright"
  export BROWSE_STATE_FILE="$_ROOT/.local_runtime/gstack/browser/browse.json"
else
  echo "gstack: run from the team workspace; see README.md" >&2
  return 1 2>/dev/null || exit 1
fi'''
    text, count = re.subn(
        r'_ROOT=\$\(git rev-parse --show-toplevel 2>/dev/null\)\r?\n'
        r'GSTACK_ROOT=[^\r\n]*\r?\n'
        r'\[ -n "\$_ROOT" \][^\r\n]*', lambda _: root_block, text)
    if count == 0:
        # Advisory/safety skills have no standard preamble, but still use helpers and state.
        end = re.match(r'\A---\r?\n.*?\r?\n---', text, re.S).end()
        text = text[:end] + '\n\n```bash\n' + root_block + '\n```\n' + text[end:]
    elif count != 1:
        raise ValueError(f'Ambiguous upstream preamble for {name}; update the adapter before installing')
    text = text.replace('_SS=".agents/skills/gstack/bin/gstack-skill-start"',
                        '_SS="$GSTACK_ROOT/bin/gstack-skill-start"')
    text = text.replace('$HOME/.agents/skills/gstack/', '$GSTACK_ROOT/')
    text = text.replace('$HOME/.codex/skills/gstack/', '$GSTACK_ROOT/')
    text = text.replace('~/.agents/skills/gstack/', '"$GSTACK_ROOT"/')
    text = text.replace('~/.codex/skills/gstack/', '"$GSTACK_ROOT"/')
    text = text.replace('$HOME/.gstack', '${GSTACK_HOME}')
    text = text.replace('~/.gstack', '"${GSTACK_HOME}"')
    if name == 'gstack-upgrade':
        end = re.match(r'\A---\r?\n.*?\r?\n---', text, re.S).end()
        note = ('\n\n## Team workspace upgrade override\n\n'
                'This project pins gstack in `tooling/gstack.lock.json`. For an upgrade request, '
                'preserve local source edits, select and record the new repository/commit/version '
                'in that lock, and run `python scripts/bootstrap.py`. See `docs/gstack.md`. '
                'The inline upgrade flow below is upstream reference; do not use it to bypass '
                'the team lock or register global skills.\n')
        text = text[:end] + note + text[end:]
    manifest_fields(text)
    return text

def register(root: Path = WORKSPACE) -> int:
    lock = load_lock(root)
    source = root / SOURCE_RELATIVE
    render = source / '.agents/skills'
    destinations = root / '.agents/skills'
    folders = sorted(p for p in render.iterdir() if p.is_dir()
                     and (p.name == 'gstack' or p.name.startswith('gstack-'))
                     and (p / 'SKILL.md').is_file())
    if len(folders) != lock['expected_skills']:
        raise ValueError(f"Expected {lock['expected_skills']} generated skills, found {len(folders)}")
    prepared = []
    for folder in folders:
        manifest = (folder / 'SKILL.md').read_text(encoding='utf-8')
        if GENERATED not in manifest:
            raise ValueError(f'Not a generated Codex skill: {folder}')
        adapted = adapt(manifest, folder.name)
        target = destinations / folder.name
        if target.exists():
            if (target / '.git').exists():
                raise ValueError('Move the old source checkout out of .agents/skills first')
            existing = target / 'SKILL.md'
            owned = (target / MARKER).is_file()
            generated = existing.is_file() and GENERATED in existing.read_text(encoding='utf-8')
            if not owned and not generated:
                raise ValueError(f'Refusing to overwrite a user-owned skill: {target}')
        prepared.append((folder, target, adapted))
    # Validate every input before touching the previous installation.
    for folder, target, adapted in prepared:
        target.mkdir(parents=True, exist_ok=True)
        for file in folder.rglob('*'):
            if not file.is_file():
                continue
            relative = file.relative_to(folder)
            if folder.name == 'gstack' and relative not in (Path('SKILL.md'), Path('agents/openai.yaml')):
                continue  # skip root runtime sidecars
            output = target / relative
            output.parent.mkdir(parents=True, exist_ok=True)
            if file.suffix == '.md':
                content = adapted if relative == Path('SKILL.md') else file.read_text(encoding='utf-8')
                output.write_text(content, encoding='utf-8', newline='\n')
            else:
                shutil.copy2(file, output)
        (target / MARKER).write_text(json.dumps({'repository': lock['repository'], 'commit': lock['commit']}) + '\n', encoding='utf-8')
    return len(prepared)

def validate_discovery(root: Path = WORKSPACE, *, require_gstack: bool = True) -> int:
    manifests = sorted((root / '.agents/skills').rglob('SKILL.md'))
    names = []
    for path in manifests:
        if path.parent.parent != root / '.agents/skills':
            raise ValueError(f'Nested/fixture skill leaked into discovery: {path.relative_to(root)}')
        name, _ = manifest_fields(path.read_text(encoding='utf-8'))
        if name != path.parent.name:
            raise ValueError(f'Skill identifier differs from its folder: {path}')
        names.append(name)
    if len(names) != len(set(names)):
        raise ValueError('Duplicate skill names')
    if 'jipdam-workflow' not in names:
        raise ValueError('The shared jipdam-workflow skill is missing')
    expected = load_lock(root)['expected_skills'] + 1
    if require_gstack and len(names) != expected:
        raise ValueError(f'Expected {expected} skills after installation, found {len(names)}')
    return len(names)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if not args.check:
        print(f'Registered {register()} gstack skills')
    print(f'Discovery verified: {validate_discovery()} unique, non-nested skills')
