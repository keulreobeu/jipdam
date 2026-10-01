"""Run model-free contracts and optionally the installed gstack browser smoke."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from team_tools import WORKSPACE, APP_RELATIVE, SOURCE_RELATIVE, git, load_lock, require_python, run, runtime_env
from register_gstack import validate_discovery

def verify_base() -> None:
    env = runtime_env()
    app = WORKSPACE / APP_RELATIVE
    run([sys.executable, '-X', 'utf8', '-m', 'unittest', 'discover', '-s', 'tests', '-v'], cwd=app, env=env)
    run([sys.executable, '-X', 'utf8', '-m', 'unittest', 'discover', '-s', 'tests', '-v'], env=env)
    runtime = WORKSPACE / '.local_runtime'
    runtime.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='team-smoke-', dir=runtime) as temporary:
        fixture = Path(temporary)
        run([sys.executable, '-X', 'utf8', 'scripts/make_synthetic_smoke.py', '--output-dir', str(fixture)], cwd=app, env=env)
        cli = [sys.executable, '-X', 'utf8', '-m', 'budongi.cli', '--db', str(fixture / 'serving.sqlite3')]
        doctor = json.loads(run([*cli, 'doctor'], cwd=app, env=env, capture=True))
        if not doctor['synthetic_only'] or doctor['ready_for_real_eval']:
            raise RuntimeError('Synthetic smoke must not be marked ready for real evaluation')
        result = json.loads(run([*cli, 'tool', '--snapshot-id', 'synthetic_toolcall_smoke_v1',
                                '--name', 'get_apartment_detail', '--arguments', '{"apartment_id":"APT_A"}'],
                               cwd=app, env=env, capture=True))
        if 'APT_A' not in json.dumps(result):
            raise RuntimeError('The synthetic detail query did not return APT_A')
    print('Application tests and model-free synthetic CLI smoke passed', flush=True)

def verify_gstack() -> None:
    actual = git(['rev-parse', 'HEAD'], cwd=WORKSPACE / SOURCE_RELATIVE, capture=True)
    if actual != load_lock()['commit']:
        raise RuntimeError('Installed gstack does not match the lock')
    print(f'Pinned gstack and {validate_discovery()} skill manifests verified', flush=True)

def verify_browser() -> None:
    binary = WORKSPACE / SOURCE_RELATIVE / ('browse/dist/browse.exe' if os.name == 'nt' else 'browse/dist/browse')
    if not binary.is_file():
        raise RuntimeError('gstack browse is not built')
    env = runtime_env()
    runtime = WORKSPACE / '.local_runtime'
    # Independent state avoids taking over an ongoing browser session.
    with tempfile.TemporaryDirectory(prefix='browser-smoke-', dir=runtime) as temporary:
        env['BROWSE_STATE_FILE'] = str(Path(temporary) / 'state/browse.json')
        try:
            run([str(binary), 'goto', 'about:blank'], env=env)
            run([str(binary), 'js', 'document.body.innerHTML="<button id=ping>Ping</button><p id=result>ready</p>";'
                 'document.querySelector("#ping").onclick=()=>document.querySelector("#result").textContent="clicked";"fixture-ready"'], env=env)
            run([str(binary), 'click', '#ping'], env=env)
            value = run([str(binary), 'js', 'document.querySelector("#result").textContent'], env=env, capture=True)
            if value.strip('"') != 'clicked':
                raise RuntimeError(f'Unexpected browser result: {value}')
            image = runtime / 'team-browser-smoke.png'
            run([str(binary), 'screenshot', str(image)], env=env)
            if not image.is_file() or image.stat().st_size == 0:
                raise RuntimeError('Browser screenshot was not created')
        finally:
            run([str(binary), 'stop'], env=env)
    print('Browser navigation, click, DOM read, screenshot, and shutdown passed', flush=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gstack', action='store_true')
    parser.add_argument('--browser', action='store_true')
    args = parser.parse_args()
    try:
        require_python()
        verify_base()
        if args.gstack or args.browser:
            verify_gstack()
        if args.browser:
            verify_browser()
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f'Verification failed: {exc}', file=sys.stderr)
        sys.exit(1)
