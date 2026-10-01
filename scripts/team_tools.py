"""Paths and process helpers for the repository's team setup commands."""
from __future__ import annotations
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

WORKSPACE = Path(__file__).resolve().parents[1]
APP_RELATIVE = Path('outputs/budongi_mvp_temp')
SOURCE_RELATIVE = Path('.local_runtime/tooling/.agents/skills/gstack')

def load_lock(root: Path = WORKSPACE) -> dict:
    lock = json.loads((root / 'tooling/gstack.lock.json').read_text(encoding='utf-8'))
    if not re.fullmatch(r'[0-9a-f]{40}', lock['commit']):
        raise ValueError('gstack lock must contain a full commit SHA')
    return lock

def runtime_env(root: Path = WORKSPACE) -> dict[str, str]:
    env = os.environ.copy()
    paths = {
        'GSTACK_ROOT': root / SOURCE_RELATIVE,
        'GSTACK_HOME': root / '.local_runtime/gstack',
        'GSTACK_PLAN_DIR': root / '.local_runtime/gstack/plans',
        'BROWSE_STATE_FILE': root / '.local_runtime/gstack/browser/browse.json',
        'PLAYWRIGHT_BROWSERS_PATH': root / '.local_runtime/playwright',
        'BUN_INSTALL_CACHE_DIR': root / '.local_runtime/bun-cache',
    }
    env.update({name: path.as_posix() for name, path in paths.items()})
    env.update(GSTACK_SKIP_FONTS='1', PYTHONUTF8='1', PYTHONPATH=str(root / APP_RELATIVE / 'src'))
    return env

def run(args: list[str], *, cwd: Path = WORKSPACE, env: dict | None = None, capture: bool = False) -> str:
    result = subprocess.run(args, cwd=cwd, env=env, check=True, text=True, encoding='utf-8',
                            errors='replace', stdout=subprocess.PIPE if capture else None)
    return result.stdout.strip() if capture else ''

def git(args: list[str], *, cwd: Path = WORKSPACE, capture: bool = False) -> str:
    return run(['git', '-c', f'safe.directory={cwd.resolve().as_posix()}',
                '-c', 'core.excludesFile=', *args], cwd=cwd, capture=capture)

def require_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RuntimeError(f'Required tool is missing: {name}. See README.md.')
    return path

def bash_executable() -> str:
    if os.name != 'nt':
        return require_tool('bash')
    executable = shutil.which('git')
    if executable:
        root = Path(executable).resolve().parents[1]
        for candidate in (root / 'bin/bash.exe', root / 'usr/bin/bash.exe'):
            if candidate.is_file():
                return str(candidate)
    raise RuntimeError('Install Git for Windows including Git Bash; WSL bash.exe is not used.')

def check_version(name: str, minimum: str) -> str:
    value = run([require_tool(name), '--version'], capture=True)
    match = re.search(r'(\d+)\.(\d+)\.(\d+)', value)
    if not match or tuple(map(int, match.groups())) < tuple(map(int, minimum.split('.'))):
        raise RuntimeError(f'{name} >= {minimum} required; found {value}')
    print(f'{name}: {value}', flush=True)
    return value

def require_python() -> None:
    if sys.version_info < (3, 11):
        raise RuntimeError('Python 3.11 or newer is required.')
