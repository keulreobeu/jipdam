"""Install the pinned project-local gstack and verify the team development environment."""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import subprocess
import sys
from team_tools import (WORKSPACE, SOURCE_RELATIVE, bash_executable, check_version,
                        git, load_lock, require_python, require_tool, run, runtime_env)
from register_gstack import register, unregister, validate_discovery
from register_claude_gstack import register_claude, unregister_claude, validate_claude_discovery

def install_gstack(host: str) -> None:
    lock = load_lock()
    require_tool('git')
    check_version('bun', lock['minimum_bun'])
    check_version('node', lock['minimum_node'])
    bash = bash_executable()
    source = WORKSPACE / SOURCE_RELATIVE
    if not source.exists():
        source.parent.mkdir(parents=True, exist_ok=True)
        git(['init', str(source)])
        git(['remote', 'add', 'origin', lock['repository']], cwd=source)
    if not (source / '.git').exists():
        raise RuntimeError('The gstack source directory is not a Git checkout; preserve it before reinstalling.')
    try:
        actual = git(['rev-parse', '--verify', '--quiet', 'HEAD'], cwd=source, capture=True)
    except subprocess.CalledProcessError:
        if any(p.name != '.git' for p in source.iterdir()):
            raise RuntimeError('Incomplete source checkout contains files; preserve them before reinstalling.')
        # Resume a failed first fetch without deleting or resetting a user's source.
        git(['fetch', '--depth', '1', lock['repository'], lock['commit']], cwd=source)
        git(['checkout', '--detach', 'FETCH_HEAD'], cwd=source)
        actual = git(['rev-parse', 'HEAD'], cwd=source, capture=True)
    if actual != lock['commit']:
        raise RuntimeError(f"Existing gstack HEAD {actual} differs from lock {lock['commit']}; preserve local edits before upgrading.")
    if (source / 'VERSION').read_text(encoding='utf-8').strip() != lock['version']:
        raise RuntimeError('The source version differs from the lock')
    git(['diff', '--quiet', 'HEAD', '--', 'package.json', 'bun.lock'], cwd=source)
    env = runtime_env()
    state = Path(env['GSTACK_HOME'])
    state.mkdir(parents=True, exist_ok=True)
    config = state / 'config.yaml'
    if not config.exists():
        config.write_text('proactive: true\ntelemetry: off\nauto_upgrade: false\nupdate_check: false\ncodex_reviews: disabled\n', encoding='utf-8')
    bun_lock = source / 'bun.lock'
    before = hashlib.sha256(bun_lock.read_bytes()).hexdigest()
    run(['bun', 'install', '--frozen-lockfile'], cwd=source, env=env)
    # The source lives in the ignored project-local runtime namespace. Setup
    # builds shared binaries/Chromium for either host without global registration.
    run([bash, '--noprofile', '--norc', './setup', '--host', host, '--prefix',
         '--no-team', '--no-plan-tune-hooks', '--no-timeline-stop-hook'], cwd=source, env=env)
    if hashlib.sha256(bun_lock.read_bytes()).hexdigest() != before:
        raise RuntimeError('Upstream setup changed bun.lock; installation is not reproducible')
    if host == 'codex':
        print(f'Registered {register()} pinned Codex gstack skills', flush=True)
        removed = unregister_claude()
        print(f'Removed {removed} installer-owned Claude skill registrations', flush=True)
        print(f'Discovery: {validate_discovery()} unique Codex/project skills', flush=True)
    else:
        claude_render = WORKSPACE / '.local_runtime/gstack/render/claude'
        run([require_tool('bun'), 'run', 'scripts/gen-skill-docs.ts', '--host', 'claude',
             '--out-dir', str(claude_render)], cwd=source, env=env)
        print(f'Registered {register_claude(WORKSPACE, claude_render)} pinned Claude gstack skills', flush=True)
        removed = unregister()
        print(f'Removed {removed} installer-owned Codex skill registrations', flush=True)
        print(f'Claude discovery: {validate_claude_discovery()} unique skills', flush=True)

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app-only', action='store_true', help='Only Python tests and synthetic CLI checks; no downloads')
    parser.add_argument('--host', choices=('codex', 'claude'), help='Host whose gstack skills should be installed (required unless --app-only)')
    parser.add_argument('--skip-verify', action='store_true', help='Install without post-install verification')
    args = parser.parse_args()
    require_python()
    if not args.app_only:
        if not args.host:
            parser.error('--host codex or --host claude is required for a full gstack installation')
        install_gstack(args.host)
    if not args.skip_verify:
        command = [sys.executable, '-X', 'utf8', str(WORKSPACE / 'scripts/verify_environment.py')]
        if not args.app_only:
            command.extend(['--gstack', '--browser', '--host', args.host])
        run(command, env=runtime_env())
    print('Team setup completed', flush=True)

if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f'Setup failed: {exc}', file=sys.stderr)
        sys.exit(1)
