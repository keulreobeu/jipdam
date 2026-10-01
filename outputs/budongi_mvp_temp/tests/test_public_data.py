from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from budongi.public_data import PublicDataError, fetch_applyhome, fetch_applyhome_models, fetch_molit


class FakeResponse:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def read(self) -> bytes:
        return self.payload


class PublicDataTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    @patch.dict("os.environ", {"DATA_GO_KR_SERVICE_KEY": "abc%2Fdef%2Bghi"})
    def test_molit_paginates_and_keeps_key_out_of_manifest(self) -> None:
        calls = []

        def open_page(request: object, *, timeout: int) -> FakeResponse:
            self.assertEqual(timeout, 20)
            query = parse_qs(urlparse(request.full_url).query)
            calls.append(query)
            number = int(query["pageNo"][0])
            payload = ("<response><header><resultCode>000</resultCode></header>"
                       "<body><items><item><aptNm>APT" + str(number) + "</aptNm></item></items>"
                       "<totalCount>2</totalCount></body></response>").encode()
            return FakeResponse(payload)

        result = fetch_molit(lawd_cd="11110", deal_ymd="202301", output_dir=self.root / "molit",
                             per_page=1, opener=open_page)
        self.assertEqual(result["row_count"], 2)
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0]["serviceKey"], ["abc/def+ghi"])
        self.assertEqual(calls[0]["DEAL_YMD"], ["202301"])
        self.assertNotIn("abc", (self.root / "molit" / "manifest.json").read_text())
        self.assertEqual(len((self.root / "molit" / "rows.jsonl").read_text().splitlines()), 2)

    @patch.dict("os.environ", {"DATA_GO_KR_SERVICE_KEY": "private-key"})
    def test_applyhome_date_filters_and_json_rows(self) -> None:
        def open_page(request: object, *, timeout: int) -> FakeResponse:
            query = parse_qs(urlparse(request.full_url).query)
            self.assertEqual(query["cond[RCRIT_PBLANC_DE::GTE]"], ["2023-01-01"])
            self.assertEqual(query["cond[RCRIT_PBLANC_DE::LTE]"], ["2023-01-31"])
            return FakeResponse(json.dumps({"data": [{"HOUSE_NM": "테스트"}], "matchCount": 1}).encode())

        result = fetch_applyhome(start_date="2023-01-01", end_date="2023-01-31",
                                 output_dir=self.root / "applyhome", opener=open_page)
        self.assertEqual(result["row_count"], 1)
        self.assertEqual(json.loads((self.root / "applyhome" / "rows.jsonl").read_text(encoding="utf-8"))["HOUSE_NM"], "테스트")
        self.assertNotIn("private-key", (self.root / "applyhome" / "manifest.json").read_text())

    @patch.dict("os.environ", {"DATA_GO_KR_SERVICE_KEY": "private-key"})
    def test_applyhome_model_uses_management_number(self) -> None:
        def open_page(request: object, *, timeout: int) -> FakeResponse:
            query = parse_qs(urlparse(request.full_url).query)
            self.assertEqual(query["cond[HOUSE_MANAGE_NO::EQ]"], ["2023820001"])
            return FakeResponse(b'{"data":[],"matchCount":0}')

        result = fetch_applyhome_models(house_manage_no="2023820001",
                                        output_dir=self.root / "models", opener=open_page)
        self.assertEqual(result["row_count"], 0)

    @patch.dict("os.environ", {"DATA_GO_KR_SERVICE_KEY": "private-key"})
    def test_api_errors_do_not_expose_key(self) -> None:
        def open_page(request: object, *, timeout: int) -> FakeResponse:
            return FakeResponse(b"<response><header><resultCode>30</resultCode>"
                                b"<resultMsg>UNREGISTERED_KEY</resultMsg></header></response>")

        with self.assertRaises(PublicDataError) as caught:
            fetch_molit(lawd_cd="11110", deal_ymd="202301", output_dir=self.root / "error",
                        opener=open_page)
        self.assertNotIn("private-key", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
