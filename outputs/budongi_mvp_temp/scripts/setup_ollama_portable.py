"""Download a hash-pinned Windows Ollama CLI into the local ignored runtime."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen


VERSION = "v0.34.4"
SHA256 = "535193f38f3344e5b08f5d1c171c31ce11aa17f0124ff69ae26d8ec7fe06fa62"
URL = f"https://github.com/ollama/ollama/releases/download/{VERSION}/ollama-windows-amd64.zip"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path(".local_runtime/ollama-v0.34.4"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    binary = args.output_dir / "ollama.exe"
    manifest_path = args.output_dir / "install_manifest.json"
    if binary.exists() and manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("archive_sha256") == SHA256 and sha256(binary) == manifest.get("exe_sha256"):
            print(f"Ready: {binary} ({VERSION}, verified installed binary)")
            return
    archive = args.output_dir / "ollama-windows-amd64.zip"
    if not archive.exists() or sha256(archive) != SHA256:
        partial = args.output_dir / "ollama-windows-amd64.zip.partial"
        request = Request(URL, headers={"User-Agent": "budongi-mvp/0.1"})
        downloaded = 0
        with urlopen(request, timeout=60) as source, partial.open("wb") as target:
            while chunk := source.read(1024 * 1024):
                target.write(chunk)
                downloaded += len(chunk)
                if downloaded // (100 * 1024 * 1024) != (downloaded - len(chunk)) // (100 * 1024 * 1024):
                    print(f"Downloaded {downloaded // (1024 * 1024)} MiB", flush=True)
        if sha256(partial) != SHA256:
            raise ValueError("Official Ollama archive SHA-256 mismatch")
        partial.replace(archive)
    with zipfile.ZipFile(archive) as bundle:
        for member in bundle.infolist():
            destination = (args.output_dir / member.filename).resolve()
            if not destination.is_relative_to(args.output_dir.resolve()):
                raise ValueError("Archive contains a path outside the runtime directory")
        bundle.extractall(args.output_dir)
    if not binary.exists():
        raise ValueError("Verified archive did not contain ollama.exe")
    manifest_path.write_text(json.dumps({"version": VERSION, "source": URL,
                                         "archive_sha256": SHA256, "exe_sha256": sha256(binary)},
                                        indent=2) + "\n", encoding="utf-8")
    archive.unlink()
    print(f"Ready: {binary} ({VERSION}, SHA-256 {SHA256})")


if __name__ == "__main__":
    main()
