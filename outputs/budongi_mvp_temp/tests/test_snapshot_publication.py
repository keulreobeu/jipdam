"""Directory publication must remain atomic and fail closed under Windows locks."""
import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from budongi.collection import publish_snapshot_directory


def windows_permission_error(code):
    error = PermissionError(13, "synthetic access denial")
    error.winerror = code
    return error


class SnapshotPublicationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / "staged"
        self.output = self.root / "output"
        self.source.mkdir()
        (self.source / "data").write_text("original", encoding="utf-8")

    def test_transient_windows_denial_retries_then_publishes(self):
        actual_rename = os.rename
        calls = []

        def rename(source, output):
            calls.append((source, output))
            if len(calls) < 3:
                raise windows_permission_error(5)
            actual_rename(source, output)

        with patch("budongi.collection.os.name", "nt"), patch("budongi.collection.os.rename", side_effect=rename), patch("budongi.collection.time.sleep") as sleep:
            publish_snapshot_directory(self.source, self.output)
        self.assertEqual(len(calls), 3)
        self.assertEqual(sleep.call_count, 2)
        self.assertFalse(self.source.exists())
        self.assertEqual((self.output / "data").read_text(encoding="utf-8"), "original")

    def test_persistent_denial_is_bounded_and_preserves_source(self):
        with patch("budongi.collection.os.name", "nt"), patch("budongi.collection.os.rename", side_effect=windows_permission_error(5)) as rename, patch("budongi.collection.time.sleep"):
            with self.assertRaises(PermissionError):
                publish_snapshot_directory(self.source, self.output)
        self.assertEqual(rename.call_count, 5)
        self.assertEqual((self.source / "data").read_text(encoding="utf-8"), "original")
        self.assertFalse(self.output.exists())

    def test_other_errors_are_not_retried(self):
        with patch("budongi.collection.os.name", "nt"), patch("budongi.collection.os.rename", side_effect=windows_permission_error(123)) as rename, patch("budongi.collection.time.sleep") as sleep:
            with self.assertRaises(PermissionError):
                publish_snapshot_directory(self.source, self.output)
        self.assertEqual(rename.call_count, 1)
        sleep.assert_not_called()

    @unittest.skipUnless(os.name == "nt", "Windows rename rejects existing destination")
    def test_existing_destination_is_never_replaced(self):
        self.output.mkdir()
        (self.output / "data").write_text("existing", encoding="utf-8")
        with self.assertRaises(OSError):
            publish_snapshot_directory(self.source, self.output)
        self.assertEqual((self.output / "data").read_text(encoding="utf-8"), "existing")
        self.assertEqual((self.source / "data").read_text(encoding="utf-8"), "original")

    @unittest.skipUnless(os.name == "nt", "requires Windows file-sharing semantics")
    def test_real_windows_lock_released_on_retry_keeps_sqlite_content(self):
        import ctypes
        from ctypes import wintypes

        database = self.source / "fixture.sqlite3"
        with closing(sqlite3.connect(database)) as connection:
            connection.execute("CREATE TABLE fixture(value INTEGER)")
            connection.execute("INSERT INTO fixture VALUES (42)")
            connection.commit()
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                      wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
        kernel.CreateFileW.restype = wintypes.HANDLE
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel.CloseHandle.restype = wintypes.BOOL
        handle = kernel.CreateFileW(str(database), 0x80000000, 3, None, 3, 0x80, None)
        self.assertNotEqual(handle, ctypes.c_void_p(-1).value, ctypes.get_last_error())
        state = {"handle": handle, "released": False}

        def release_lock(_delay):
            self.assertFalse(state["released"])
            self.assertTrue(kernel.CloseHandle(state["handle"]))
            state["released"] = True

        try:
            with self.assertRaises(PermissionError) as denied:
                os.rename(self.source, self.output)
            self.assertEqual(denied.exception.winerror, 5)
            with patch("budongi.collection.time.sleep", side_effect=release_lock):
                publish_snapshot_directory(self.source, self.output)
            self.assertTrue(state["released"])
            with closing(sqlite3.connect((self.output / database.name).as_uri() + "?mode=ro", uri=True)) as connection:
                self.assertEqual(connection.execute("SELECT value FROM fixture").fetchall(), [(42,)])
        finally:
            if not state["released"]:
                kernel.CloseHandle(state["handle"])


if __name__ == "__main__":
    unittest.main()
