"""Package only Git-selected team source files, without local runtimes or Git metadata."""
from __future__ import annotations
import argparse
from pathlib import Path
import subprocess
import sys
import zipfile
from team_tools import WORKSPACE, git

def source_files() -> list[Path]:
    listing = git(['ls-files', '-z', '--cached', '--others', '--exclude-standard'], capture=True)
    paths = sorted(set(path for path in listing.split('\0') if path))
    result = []
    for name in paths:
        relative = Path(name)
        file = WORKSPACE / relative
        if not file.is_file() or not file.resolve().is_relative_to(WORKSPACE):
            raise ValueError(f'Unexpected shared path: {relative}')
        if any(part in ('.git', '.local_runtime', 'node_modules', '__pycache__', '.venv') for part in relative.parts):
            raise ValueError(f'A local artifact is tracked or not ignored: {relative}')
        if relative.parts[0] == 'work' or (relative.parts[:2] == ('.agents', 'skills') and relative.parts[2].startswith('gstack')):
            raise ValueError(f'Archive/source gstack must not be shared as a nested checkout: {relative}')
        if file.name == '.env' or (file.name.startswith('.env.') and file.name != '.env.example'):
            raise ValueError(f'Environment file must not be packaged: {relative}')
        if file.suffix in ('.db', '.sqlite3'):
            raise ValueError(f'Database must not be packaged: {relative}')
        result.append(relative)
    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=WORKSPACE / '.local_runtime/team-share/jipdam-team-source.zip')
    args = parser.parse_args()
    try:
        output = args.output.resolve()
        if not output.is_relative_to(WORKSPACE / '.local_runtime'):
            raise ValueError('Export ZIP must be written under .local_runtime to avoid packaging itself')
        files = source_files()
        output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
            for relative in files:
                archive.write(WORKSPACE / relative, relative.as_posix())
        print(f'{len(files)} source files, {output.stat().st_size} bytes: {output}')
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f'Export failed: {exc}', file=sys.stderr)
        sys.exit(1)
