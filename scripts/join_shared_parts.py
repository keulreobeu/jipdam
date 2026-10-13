"""Join verified portable ZIP parts without overwriting existing files."""
import argparse
import hashlib
import json
from pathlib import Path


def join_parts(manifest: Path, output: Path) -> str:
    data = json.loads(manifest.read_text(encoding='utf-8'))
    if data.get('schema_version') != 'jipdam_zip_parts_v1' or not data.get('parts'):
        raise ValueError('Invalid parts manifest')
    if output.exists():
        raise ValueError('Output already exists')
    paths = []
    for part in data['parts']:
        name = part['name']
        if name != Path(name).name or any(x in name for x in ('/', '\\', ':')) or name in {'.', '..'}:
            raise ValueError('Unsafe part path')
        paths.append(manifest.parent / name)
    if len(set(paths)) != len(paths):
        raise ValueError('Duplicate part')
    total = hashlib.sha256()
    size = 0
    with output.open('xb') as out:
        for path, part in zip(paths, data['parts']):
            current = hashlib.sha256()
            count = 0
            with path.open('rb') as stream:
                for payload in iter(lambda: stream.read(1024 * 1024), b''):
                    current.update(payload)
                    total.update(payload)
                    out.write(payload)
                    count += len(payload)
            if count != part['bytes'] or current.hexdigest() != part['sha256']:
                raise ValueError('Part hash mismatch; incomplete output is not a verified ZIP')
            size += count
    if size != data['bytes'] or total.hexdigest() != data['sha256']:
        raise ValueError('Whole ZIP hash mismatch')
    return total.hexdigest()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        print(join_parts(args.manifest, args.output))
    except (ValueError, OSError) as exc:
        parser.exit(2, str(exc) + '\n')
