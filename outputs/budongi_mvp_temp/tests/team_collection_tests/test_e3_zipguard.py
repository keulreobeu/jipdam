import tempfile
import unittest
import zipfile
import zlib
from pathlib import Path

from budongi.team_collection import contract as C
from budongi.team_collection.readers.zipguard import extract_member, list_members

CP949 = "자료.csv".encode("cp949")  # 8 bytes, stored without the UTF-8 flag


def build(path, entries):
    """entries: (name, data, compress_type, raw_name_bytes_or_None); raw replaces the ASCII placeholder."""
    with zipfile.ZipFile(path, "w") as zf:
        for name, data, ct, _raw in entries:
            info = zipfile.ZipInfo(name)
            info.flag_bits = 0
            info.compress_type = ct
            zf.writestr(info, data)
    blob = Path(path).read_bytes()
    for name, _d, _c, raw in entries:
        if raw is not None:
            ph = name.encode("ascii")
            assert len(ph) == len(raw) and blob.count(ph) == 2
            blob = blob.replace(ph, raw)
    Path(path).write_bytes(blob)
    return path


S = zipfile.ZIP_STORED
D = zipfile.ZIP_DEFLATED


class TestE3ListMembers(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_names_and_encodings(self):
        z = build(self.dir / "a.zip", [("a/b.txt", b"1", S, None), ("한글.txt", b"2", D, None),
                                       ("QQQQ.csv", b"3", S, CP949)])
        got = list_members(z)
        self.assertEqual([m["name"] for m in got], ["a/b.txt", "한글.txt", "자료.csv"])
        self.assertEqual([m["encoding"] for m in got], ["ascii", "utf-8", "cp949"])

    def test_entry_fields(self):
        z = build(self.dir / "a.zip", [("x.txt", b"hello", S, None)])
        self.assertEqual(list_members(z), [{
            "name": "x.txt", "encoding": "ascii", "size": 5, "compressed_size": 5,
            "crc": zlib.crc32(b"hello"), "is_dir": False, "encrypted": False, "safe": True}])

    def test_zip_slip_listed_unsafe(self):
        z = build(self.dir / "a.zip", [("../evil.txt", b"x", S, None), ("ok.txt", b"y", S, None)])
        self.assertEqual([m["safe"] for m in list_members(z)], [False, True])


class TestE3ExtractMember(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.out = self.dir / "out"
        self.out.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def code(self, *args, **kw):
        with self.assertRaises(C.ContractError) as cm:
            extract_member(*args, **kw)
        return str(cm.exception)

    def test_extract_nested(self):
        z = build(self.dir / "a.zip", [("sub/x.txt", b"hello", D, None)])
        p = extract_member(z, "sub/x.txt", self.out, max_bytes=100)
        self.assertEqual(Path(p), self.out / "sub" / "x.txt")
        self.assertEqual(Path(p).read_bytes(), b"hello")

    def test_extract_cp949_member(self):
        z = build(self.dir / "a.zip", [("QQQQ.csv", b"a,b\n", S, CP949)])
        p = extract_member(z, "자료.csv", self.out, max_bytes=100)
        self.assertEqual(Path(p).read_bytes(), b"a,b\n")
        self.assertEqual(Path(p).name, "자료.csv")

    def test_zip_slip_rejected(self):
        z = build(self.dir / "a.zip", [("../evil.txt", b"x", S, None)])
        self.assertEqual(self.code(z, "../evil.txt", self.out, max_bytes=100), "unsafe_member_name")
        self.assertFalse((self.dir / "evil.txt").exists())

    def test_target_exists(self):
        z = build(self.dir / "a.zip", [("x.txt", b"new", S, None)])
        (self.out / "x.txt").write_bytes(b"old")
        self.assertEqual(self.code(z, "x.txt", self.out, max_bytes=100), "target_exists")
        self.assertEqual((self.out / "x.txt").read_bytes(), b"old")

    def test_ratio_default_rejected(self):
        z = build(self.dir / "a.zip", [("z.bin", b"\0" * 300000, D, None)])
        self.assertEqual(self.code(z, "z.bin", self.out, max_bytes=10 ** 6),
                         "compression_ratio_exceeded")


if __name__ == "__main__":
    unittest.main()
