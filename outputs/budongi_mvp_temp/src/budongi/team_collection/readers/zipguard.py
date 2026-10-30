"""Guarded ZIP member listing and extraction."""
from __future__ import annotations

import math
import os
from pathlib import Path
import zipfile
import zlib

from budongi.team_collection import contract as C


def _decode_member_name(info: zipfile.ZipInfo) -> tuple[str, str]:
    if info.flag_bits & 0x800:
        return info.orig_filename, "utf-8"
    raw = info.orig_filename.encode("cp437")
    if all(b < 0x80 for b in raw):
        return raw.decode("ascii"), "ascii"
    try:
        return raw.decode("cp949"), "cp949"
    except UnicodeDecodeError:
        return raw.decode("cp437"), "cp437"


def _is_safe_name(name: str) -> bool:
    if not name:
        return False
    if name.startswith("/"):
        return False
    if len(name) >= 2 and ("a" <= name[0] <= "z" or "A" <= name[0] <= "Z") and name[1] == ":":
        return False
    if "\\" in name:
        return False
    stripped = name[:-1] if name.endswith("/") else name
    parts = stripped.split("/")
    if any(p in ("", ".", "..") for p in parts):
        return False
    return True


def list_members(path: str | os.PathLike) -> list[dict]:
    """Return one dict per central-directory entry with decoded name and header facts."""
    if not isinstance(path, (str, os.PathLike)):
        raise C.ContractError("invalid_zip")
    try:
        if Path(path).is_dir():
            raise C.ContractError("invalid_zip")
        with zipfile.ZipFile(path, "r") as zf:
            members = []
            for info in zf.infolist():
                name, encoding = _decode_member_name(info)
                safe = _is_safe_name(name)
                is_dir = name.endswith("/")
                encrypted = bool(info.flag_bits & 0x1)
                members.append({
                    "name": name,
                    "encoding": encoding,
                    "size": info.file_size,
                    "compressed_size": info.compress_size,
                    "crc": info.CRC,
                    "is_dir": is_dir,
                    "encrypted": encrypted,
                    "safe": safe,
                })
            return members
    except (OSError, zipfile.BadZipFile):
        raise C.ContractError("invalid_zip")


def extract_member(
    path: str | os.PathLike,
    name: str,
    dest: str | os.PathLike,
    *,
    max_bytes: int,
    max_ratio: float = 100,
) -> Path:
    """Safely extract one member by decoded name into dest and return its path."""
    if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes < 1:
        raise C.ContractError("invalid_limit")
    if (
        isinstance(max_ratio, bool)
        or not isinstance(max_ratio, (int, float))
        or not math.isfinite(max_ratio)
        or max_ratio <= 0
    ):
        raise C.ContractError("invalid_limit")

    if not isinstance(dest, (str, os.PathLike)):
        raise C.ContractError("invalid_dest")
    try:
        dest_path = Path(dest)
        if not dest_path.is_dir():
            raise C.ContractError("invalid_dest")
    except OSError:
        raise C.ContractError("invalid_dest")

    if not isinstance(path, (str, os.PathLike)):
        raise C.ContractError("invalid_zip")
    try:
        if Path(path).is_dir():
            raise C.ContractError("invalid_zip")
        zf = zipfile.ZipFile(path, "r")
    except (OSError, zipfile.BadZipFile):
        raise C.ContractError("invalid_zip")

    with zf:
        matching = []
        for info in zf.infolist():
            decoded_name, _ = _decode_member_name(info)
            if decoded_name == name:
                matching.append(info)

        if len(matching) == 0:
            raise C.ContractError("member_not_found")
        if len(matching) > 1:
            raise C.ContractError("duplicate_member")
        matched_info = matching[0]

        if not _is_safe_name(name):
            raise C.ContractError("unsafe_member_name")
        if name.endswith("/"):
            raise C.ContractError("member_is_directory")
        if matched_info.flag_bits & 0x1:
            raise C.ContractError("encrypted_member")
        if matched_info.file_size > max_bytes:
            raise C.ContractError("member_too_large")
        if matched_info.file_size > max_ratio * max(matched_info.compress_size, 1):
            raise C.ContractError("compression_ratio_exceeded")

        dest_resolved = dest_path.resolve()
        target = Path(dest, *name.split("/"))
        try:
            target_resolved = target.resolve()
            rel = target_resolved.relative_to(dest_resolved)
            if str(rel) in (".", ""):
                raise C.ContractError("unsafe_member_name")
        except (ValueError, OSError):
            raise C.ContractError("unsafe_member_name")

        if target.exists() or target.is_symlink():
            raise C.ContractError("target_exists")

        curr = target.parent
        parents_to_check = []
        while True:
            try:
                if curr == dest_path or curr.resolve() == dest_resolved:
                    break
            except OSError:
                break
            parents_to_check.append(curr)
            curr = curr.parent

        for p in reversed(parents_to_check):
            if (p.exists() or p.is_symlink()) and not p.is_dir():
                raise C.ContractError("target_exists")

        try:
            target.parent.mkdir(parents=True, exist_ok=True)
        except (FileExistsError, NotADirectoryError, OSError):
            raise C.ContractError("target_exists")

        target_created = False
        success = False
        try:
            with zf.open(matched_info, "r") as src:
                try:
                    with open(target, "xb") as dst:
                        target_created = True
                        written_bytes = 0
                        crc = 0
                        while True:
                            chunk = src.read(65536)
                            if not chunk:
                                break
                            written_bytes += len(chunk)
                            if written_bytes > max_bytes:
                                raise C.ContractError("member_too_large")
                            crc = zlib.crc32(chunk, crc)
                            dst.write(chunk)
                        if crc != matched_info.CRC:
                            raise C.ContractError("crc_mismatch")
                        success = True
                except (FileExistsError, NotADirectoryError):
                    raise C.ContractError("target_exists")
        except zipfile.BadZipFile:
            raise C.ContractError("crc_mismatch")
        finally:
            if target_created and not success:
                try:
                    target.unlink(missing_ok=True)
                except OSError:
                    pass

        return target
