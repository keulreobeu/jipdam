import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from budongi.team_collection.package.zipper import split_parts, write_zip

STAMP = (2026, 10, 29, 12, 0, 0)
ROOT = "s1/b-20261029-v1"


def _sha(data):
    return hashlib.sha256(data).hexdigest()


class WriteZipTypicalTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.src = self.base / "src"
        (self.src / "a").mkdir(parents=True)
        (self.src / "b.txt").write_bytes(b"bee")
        (self.src / "a" / "z.txt").write_bytes(b"zed")
        (self.src / "a.txt").write_bytes(b"ay")

    def tearDown(self):
        self._tmp.cleanup()

    def test_members_order_and_contents(self):
        dest = self.base / "out.zip"
        result = write_zip(self.src, dest, arc_root=ROOT, stamp=STAMP)
        expected = [ROOT + "/a.txt", ROOT + "/a/z.txt", ROOT + "/b.txt"]
        self.assertEqual(result["members"], expected)
        with zipfile.ZipFile(dest) as zf:
            self.assertEqual(zf.namelist(), expected)
            self.assertIsNone(zf.testzip())
            self.assertEqual(zf.read(ROOT + "/a/z.txt"), b"zed")
            self.assertEqual(zf.read(ROOT + "/b.txt"), b"bee")

    def test_return_describes_file(self):
        dest = self.base / "out.zip"
        result = write_zip(self.src, dest, arc_root=ROOT, stamp=STAMP)
        data = dest.read_bytes()
        self.assertEqual(result["bytes"], len(data))
        self.assertEqual(result["sha256"], _sha(data))


class SplitPartsTypicalTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.data = b"0123456789"
        self.path = self.base / "x.zip"
        self.path.write_bytes(self.data)

    def tearDown(self):
        self._tmp.cleanup()

    def test_parts_and_manifest(self):
        manifest = split_parts(self.path, part_bytes=4)
        self.assertEqual(manifest["schema_version"], "jipdam_zip_parts_v1")
        self.assertEqual(manifest["name"], "x.zip")
        self.assertEqual(manifest["bytes"], 10)
        self.assertEqual(manifest["sha256"], _sha(self.data))
        names = [p["name"] for p in manifest["parts"]]
        self.assertEqual(names, ["x.zip.part001", "x.zip.part002", "x.zip.part003"])
        self.assertEqual([p["bytes"] for p in manifest["parts"]], [4, 4, 2])
        chunks = [self.data[0:4], self.data[4:8], self.data[8:10]]
        for part, chunk in zip(manifest["parts"], chunks):
            self.assertEqual((self.base / part["name"]).read_bytes(), chunk)
            self.assertEqual(part["sha256"], _sha(chunk))

    def test_manifest_file_and_join(self):
        manifest = split_parts(self.path, part_bytes=4)
        stored = json.loads((self.base / "x.zip.parts.json").read_text(encoding="utf-8"))
        self.assertEqual(stored, manifest)
        joined = b"".join((self.base / p["name"]).read_bytes() for p in stored["parts"])
        self.assertEqual(joined, self.data)
        self.assertEqual(self.path.read_bytes(), self.data)


if __name__ == "__main__":
    unittest.main()
