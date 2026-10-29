"""Lead shells: key handles, secret sweep and GitHub overlap search (no network, no real keys)."""
from __future__ import annotations

import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from budongi.team_collection import contract as C
from budongi.team_collection.credentials import opened, resolve
from budongi.team_collection.issues_net import fetch_issues, find_overlaps, next_number
from budongi.team_collection.secret_sweep import sweep_tree, sweep_zip

CID = "12345678-1234-1234-1234-123456789abc"
KEY = "AbC123%2Bxyz%3D%3Dkey9876"


class FakeVault:
    def __init__(self, secret=KEY, error=None):
        self.secret, self.error, self.calls = secret, error, []

    def get_secret(self, credential_id, *, expected_provider_id=None):
        self.calls.append((credential_id, expected_provider_id))
        if self.error:
            raise self.error
        return self.secret


class CredentialTests(unittest.TestCase):
    def test_handle_hides_key_and_is_cleared(self):
        vault = FakeVault()
        with opened({"datagokr": CID}, vault=vault, expected_providers={"datagokr": None}) as handles:
            handle = handles["datagokr"]
            self.assertEqual(handle.reveal(), "AbC123+xyz==key9876")
            self.assertNotIn("AbC", repr(handle))
            self.assertEqual(len(handle.key_ref), 64)
        with self.assertRaisesRegex(C.ContractError, "credential_cleared"):
            handle.reveal()

    def test_bad_ids_and_vault_errors_fail_closed(self):
        with self.assertRaisesRegex(C.ContractError, "invalid_opaque_credential_id"):
            resolve({"x": "not-an-id"}, vault=FakeVault())
        with self.assertRaisesRegex(C.ContractError, "credential_unavailable"):
            resolve({"x": CID}, vault=FakeVault(error=RuntimeError("secret detail")))
        with self.assertRaisesRegex(C.ContractError, "credential_contains_internal_whitespace"):
            resolve({"x": CID}, vault=FakeVault(secret="ab cd efgh"))


class SweepTests(unittest.TestCase):
    def test_key_forms_and_patterns_are_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ok.json").write_text('{"url": "http://openapi.seoul.go.kr:8088/{KEY}/json/x/1/5/"}', encoding="utf-8")
            (root / "leak.txt").write_text("key AbC123+xyz==key9876 here", encoding="utf-8")
            (root / "url.txt").write_text("https://apis.data.go.kr/x?serviceKey=ZZZZZZZZZZ", encoding="utf-8")
            self.assertEqual(sweep_tree(root, ["AbC123+xyz==key9876"]), ["leak.txt", "url.txt"])
            archive = root / "p.zip"
            with zipfile.ZipFile(archive, "w") as zf:
                zf.writestr("a/clean.json", "{}")
                zf.writestr("a/enc.txt", "AbC123%2Bxyz%3D%3Dkey9876")
            self.assertEqual(sweep_zip(archive, ["AbC123+xyz==key9876"]), ["a/enc.txt"])


class FakeGitHub:
    def __init__(self, pages):
        self.pages = list(pages)

    def open(self, request, timeout=None):
        self.last = request
        return io.BytesIO(json.dumps(self.pages.pop(0)).encode("utf-8"))


class IssueSearchTests(unittest.TestCase):
    def test_fetch_without_auth_and_overlap_by_dataset_id(self):
        issues = [{"number": 41, "title": "[수집] 1~8호선 15099316", "state": "open", "body": None, "labels": []},
                  {"number": 34, "title": "PR", "state": "closed", "body": "x", "labels": [], "pull_request": {}}]
        gh = FakeGitHub([issues])
        items = fetch_issues(opener=gh)
        self.assertFalse(gh.last.has_header("Authorization"))
        self.assertEqual(next_number(items), 42)
        self.assertEqual([h["number"] for h in find_overlaps({"dataset_id": "15099316"}, items)], [41])
        self.assertEqual(find_overlaps({"dataset_id": "OA-15067"}, items), [])


if __name__ == "__main__":
    unittest.main()
