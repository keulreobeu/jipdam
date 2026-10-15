"""Download a previously verified Jipdam data package from Google Drive."""
from __future__ import annotations

import argparse
import hashlib
from html.parser import HTMLParser
import http.cookiejar
import json
import os
import re
import shutil
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


USER_AGENT = 'JipdamPortableData/1.0 (+https://github.com/keulreobeu/jipdam)'

PACKAGES = {
    'statistics': {
        'archive_name': 'kb-statistics-provided-20261013-portable-v1.zip',
        'bytes': 87135693,
        'sha256': '83f0e40ac834bcb5a468fa51243913e7d73fc87d7d8eb15d279cca27dcdc32e1',
        'files': [
            {
                'id': '1SQot8SCZXC-MdketgQPyoyROADwPWnbP',
                'name': 'kb-statistics-provided-20261013-portable-v1.zip',
                'bytes': 87135693,
                'sha256': '83f0e40ac834bcb5a468fa51243913e7d73fc87d7d8eb15d279cca27dcdc32e1',
            },
        ],
    },
    'molit': {
        'archive_name': 'molit-seoul-three-api-20261012-portable-v2.zip',
        'bytes': 210915139,
        'sha256': 'e9eeb0c1057e16f11066c42e704ffd38d88e93bc59dda797a3b250c7366cc013',
        'files': [
            {
                'id': '1wvA1exd635p1lVZzfrojvlCUGASK4-Ph',
                'name': 'molit-seoul-three-api-20261012-portable-v2.zip.part001',
                'bytes': 83886080,
                'sha256': 'bae5d54730e29db852e4a485c2b66487174e500a2cee43abe5428ca54f59064f',
            },
            {
                'id': '1oqJiUgFFRM18OsL_MPT7M6elDVIsx6A5',
                'name': 'molit-seoul-three-api-20261012-portable-v2.zip.part002',
                'bytes': 83886080,
                'sha256': 'd0f2b3c7a484cf20daa6ee8d2e7e538fc7ea175a4dd7acc639c4b6731c32f3cb',
            },
            {
                'id': '15RprzVeERz5x9SwH1p6toYTCUJVmXs_V',
                'name': 'molit-seoul-three-api-20261012-portable-v2.zip.part003',
                'bytes': 43142979,
                'sha256': '0062106f7b600eda2a337e6ccc000d00e302d773eda285d2e1173adf7dbc31e6',
            },
        ],
    },
}


def _download_url(file_id: str, token: str | None = None) -> str:
    query = {'export': 'download', 'id': file_id}
    if token:
        query['confirm'] = token
    return 'https://drive.google.com/uc?' + urllib.parse.urlencode(query)


def _confirm_token(page: str) -> str | None:
    patterns = (
        r'[?&]confirm=([0-9A-Za-z_-]+)',
        r'name="confirm"\s+value="([0-9A-Za-z_-]+)"',
    )
    for pattern in patterns:
        match = re.search(pattern, page)
        if match:
            return match.group(1)
    return None


def _confirmation_url(page: str, file_id: str) -> str:
    """Follow only the observed Drive download form, preserving its UUID."""
    class Form(HTMLParser):
        def __init__(self):
            super().__init__()
            self.action = None
            self.fields = {}
            self.inside = False
        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if tag == 'form' and attrs.get('id') == 'download-form':
                self.action = attrs.get('action')
                self.inside = attrs.get('method', 'get').lower() == 'get'
            if tag == 'input' and self.inside and attrs.get('type') == 'hidden':
                name = attrs.get('name')
                if name in {'id', 'export', 'confirm', 'uuid'}:
                    self.fields[name] = attrs.get('value', '')
        def handle_endtag(self, tag):
            if tag == 'form': self.inside = False
    form = Form()
    form.feed(page)
    if form.action:
        if (form.action != 'https://drive.usercontent.google.com/download'
                or form.fields.get('id') != file_id or form.fields.get('export') != 'download'
                or not form.fields.get('confirm')):
            raise ValueError('Drive confirmation form has an unsupported target or file ID')
        return form.action + '?' + urllib.parse.urlencode(form.fields)
    token = _confirm_token(page)
    if not token:
        raise ValueError('Drive did not return a download confirmation; check link access')
    return _download_url(file_id, token)


def download_file(file: dict, destination: Path, opener: urllib.request.OpenerDirector) -> None:
    digest = hashlib.sha256()
    count = 0
    request = urllib.request.Request(_download_url(file['id']), headers={'User-Agent': USER_AGENT})
    response = opener.open(request, timeout=60)
    content_type = response.headers.get_content_type()
    if content_type == 'text/html':
        with response:
            page = response.read(2 * 1024 * 1024).decode('utf-8', errors='replace')
        request = urllib.request.Request(_confirmation_url(page, file['id']), headers={'User-Agent': USER_AGENT})
        response = opener.open(request, timeout=60)
        content_type = response.headers.get_content_type()
        if content_type == 'text/html':
            response.close()
            raise ValueError(f"Drive download confirmation did not produce a file for {file['name']}")

    with response, destination.open('xb') as output:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            output.write(chunk)
            digest.update(chunk)
            count += len(chunk)

    if count != file['bytes'] or digest.hexdigest() != file['sha256']:
        raise ValueError(f"Downloaded file hash/size mismatch: {file['name']}")


def download_package(name: str, destination: Path) -> list[Path]:
    package = PACKAGES[name]
    target = destination.expanduser().resolve()
    if target.exists():
        raise ValueError('Output directory already exists; choose a new path')
    target.parent.mkdir(parents=True, exist_ok=True)

    cookie_jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
    with tempfile.TemporaryDirectory(prefix='.jipdam-download-', dir=target.parent) as temporary:
        stage = Path(temporary) / 'package'
        stage.mkdir()
        downloaded = []
        for file in package['files']:
            path = stage / file['name']
            download_file(file, path, opener)
            downloaded.append(path)

        if name == 'molit':
            manifest = {
                'schema_version': 'jipdam_zip_parts_v1',
                'original_name': package['archive_name'],
                'bytes': package['bytes'],
                'sha256': package['sha256'],
                'parts': [
                    {'name': f['name'], 'bytes': f['bytes'], 'sha256': f['sha256']}
                    for f in package['files']
                ],
            }
            manifest_path = stage / (package['archive_name'] + '.parts.json')
            manifest_path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
            archive_path = stage / package['archive_name']
            with archive_path.open('xb') as output:
                total = hashlib.sha256()
                size = 0
                for part in downloaded:
                    with part.open('rb') as source:
                        shutil.copyfileobj(source, output, length=1024 * 1024)
                    with part.open('rb') as source:
                        for chunk in iter(lambda: source.read(1024 * 1024), b''):
                            total.update(chunk)
                            size += len(chunk)
            if size != package['bytes'] or total.hexdigest() != package['sha256']:
                raise ValueError('Reassembled MOLIT package hash/size mismatch')

        if target.exists():
            raise ValueError('Output directory appeared during download; choose a new path')
        os.replace(stage, target)

    paths = [target / file['name'] for file in package['files']]
    archive = target / package['archive_name']
    return paths if archive in paths else [*paths, archive]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package', choices=sorted(PACKAGES))
    parser.add_argument('--output', type=Path, required=True, help='New directory for the verified download')
    args = parser.parse_args()
    try:
        files = download_package(args.package, args.output)
        print(json.dumps({'status': 'verified', 'package': args.package, 'files': [str(p) for p in files]}, ensure_ascii=False))
    except (OSError, ValueError, urllib.error.URLError) as exc:
        parser.exit(2, f'Download failed: {exc}\n')


if __name__ == '__main__':
    main()
