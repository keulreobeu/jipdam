"""Small storage primitives shared by the catalog and coordinator."""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


class PipelineError(ValueError):
    """Safe public error code (never a raw source value)."""

    def __init__(self, code, evidence=None):
        super().__init__(code)
        self.evidence = evidence


class ExecutionFailure(PipelineError):
    """An attempt was started, as distinct from a rejected precondition."""


def now():
    return datetime.now(timezone.utc).isoformat()


def dumps(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def signature(value):
    return hashlib.sha256(dumps(value).encode("utf-8")).hexdigest()


def sha_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,119}", value):
        raise PipelineError("invalid_identifier")
    return value


def checked_path(value):
    path = Path(value).absolute()
    for part in [path, *path.parents]:
        if part.is_symlink():
            raise PipelineError("symlink_path_forbidden")
        try:
            if getattr(part.lstat(), "st_file_attributes", 0) & 0x400:
                raise PipelineError("symlink_or_reparse_path_forbidden")
        except FileNotFoundError:
            pass
    return path.resolve()


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (ValueError, OSError, UnicodeError):
        raise PipelineError("invalid_json_file") from None


def atomic_json(path, value):
    path = checked_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".pipeline-", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(dumps(value) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


@contextmanager
def writer_lock(root):
    """OS lock releases on process death; no stale PID guessing or lock deletion."""
    root = checked_path(root)
    root.mkdir(parents=True, exist_ok=True)
    path = root / ".writer.lock"
    checked_path(path)
    with path.open("a+b") as stream:
        if path.stat().st_size == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise PipelineError("catalog_writer_busy") from None
        try:
            yield root
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream, fcntl.LOCK_UN)
