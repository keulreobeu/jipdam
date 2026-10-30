"""Deterministic package ZIP writer and ZIP parts splitter."""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import zipfile
from pathlib import Path

from budongi.team_collection import contract as C

_CHUNK = 1024 * 1024
_FILE_ATTR = 0o100644 << 16


def _valid_arc_root(arc_root: object) -> bool:
    if not isinstance(arc_root, str) or not arc_root:
        return False
    for part in arc_root.split("/"):
        if not part or part in (".", ".."):
            return False
        if "\\" in part or ":" in part:
            return False
    return True


def _valid_stamp(stamp: object) -> bool:
    if not isinstance(stamp, tuple) or len(stamp) != 6:
        return False
    for item in stamp:
        if type(item) is not int:
            return False
    try:
        datetime.datetime(*stamp)
    except (ValueError, OverflowError, TypeError):
        return False
    return 1980 <= stamp[0] <= 2107


def _collect_files(src: Path) -> list[tuple[str, Path]]:
    found: list[tuple[str, Path]] = []
    for root, _dirs, names in os.walk(src):
        root_path = Path(root)
        for name in names:
            full = root_path / name
            if full.is_symlink() or not full.is_file():
                continue
            rel = full.relative_to(src).as_posix()
            found.append((rel, full))
    found.sort(key=lambda item: item[0])
    return found


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(_CHUNK)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def write_zip(src: Path, dest: Path, *, arc_root: str,
              stamp: tuple[int, int, int, int, int, int]) -> dict:
    """Write every regular file under src into a new deterministic ZIP at dest."""
    if not _valid_arc_root(arc_root):
        raise C.ContractError("invalid_arc_root")
    if not _valid_stamp(stamp):
        raise C.ContractError("invalid_stamp")
    src = Path(src)
    dest = Path(dest)
    if not src.is_dir():
        raise C.ContractError("src_not_directory")
    if os.path.lexists(dest):
        raise C.ContractError("dest_exists")
    if not dest.parent.is_dir():
        raise C.ContractError("dest_parent_missing")
    src_resolved = src.resolve()
    dest_resolved = dest.resolve()
    if dest_resolved == src_resolved or src_resolved in dest_resolved.parents:
        raise C.ContractError("dest_inside_src")
    files = _collect_files(src)
    if not files:
        raise C.ContractError("empty_source")

    members: list[str] = []
    try:
        with open(dest, "xb") as handle:
            with zipfile.ZipFile(handle, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for rel, full in files:
                    name = arc_root + "/" + rel
                    info = zipfile.ZipInfo(filename=name, date_time=stamp)
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.create_system = 3
                    info.external_attr = _FILE_ATTR
                    info.file_size = full.stat().st_size
                    with open(full, "rb") as reader, zf.open(info, "w") as writer:
                        while True:
                            chunk = reader.read(_CHUNK)
                            if not chunk:
                                break
                            writer.write(chunk)
                    members.append(name)
    except FileExistsError:
        raise C.ContractError("dest_exists")
    except Exception:
        try:
            if dest.exists():
                dest.unlink()
        except OSError:
            pass
        raise
    return {
        "bytes": dest.stat().st_size,
        "sha256": _file_sha256(dest),
        "members": members,
    }


def split_parts(path: Path, *, part_bytes: int | None = None) -> dict:
    """Split the file at path into numbered part files and write its parts manifest."""
    path = Path(path)
    if not path.is_file():
        raise C.ContractError("zip_not_found")
    size = path.stat().st_size
    if size == 0:
        raise C.ContractError("empty_zip")
    if part_bytes is None:
        part_bytes = C.PART_BYTES
    if not isinstance(part_bytes, int) or isinstance(part_bytes, bool) or part_bytes < 1:
        raise C.ContractError("invalid_part_bytes")
    count = -(-size // part_bytes)
    if count > 999:
        raise C.ContractError("too_many_parts")
    parent = path.parent
    part_names = [f"{path.name}.part{index:03d}" for index in range(1, count + 1)]
    manifest_path = parent / (path.name + ".parts.json")
    for target in [parent / name for name in part_names] + [manifest_path]:
        if os.path.lexists(target):
            raise C.ContractError("part_exists")

    whole = hashlib.sha256()
    total = 0
    parts: list[dict] = []
    created: list[Path] = []
    try:
        with open(path, "rb") as reader:
            for name in part_names:
                part_digest = hashlib.sha256()
                written = 0
                target = parent / name
                with open(target, "xb") as writer:
                    created.append(target)
                    while written < part_bytes:
                        chunk = reader.read(min(_CHUNK, part_bytes - written))
                        if not chunk:
                            break
                        writer.write(chunk)
                        part_digest.update(chunk)
                        whole.update(chunk)
                        written += len(chunk)
                total += written
                parts.append({"name": name, "bytes": written,
                              "sha256": part_digest.hexdigest()})
        manifest = {
            "schema_version": "jipdam_zip_parts_v1",
            "name": path.name,
            "bytes": total,
            "sha256": whole.hexdigest(),
            "parts": parts,
        }
        text = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)
        with open(manifest_path, "xb") as writer:
            created.append(manifest_path)
            writer.write(text.encode("utf-8") + b"\n")
    except Exception:
        for target in created:
            try:
                target.unlink()
            except OSError:
                pass
        raise
    return manifest
