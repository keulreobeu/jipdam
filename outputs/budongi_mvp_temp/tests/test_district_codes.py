from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from budongi.district_codes import district_for_address, official_districts
from scripts.fetch_catalog_trades_2023 import verify_copy
from scripts.report_catalog_trade_matches import _address_parts


class DistrictCodeTests(unittest.TestCase):
    def test_official_codes_and_address_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / "codes.zip"
            table = "법정동코드\t법정동명\t폐지여부\n" + "\n".join([
                "4122000000\t경기도 평택시\t존재",
                "4133000000\t경기도 평택시\t폐지",
                "4115000000\t경기도 의정부시\t존재",
                "1111000000\t서울특별시 종로구\t존재",
                "4117300000\t경기도 성남시 수정구\t존재",
            ])
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr("codes.txt", table.encode("cp949"))
            districts, digest = official_districts(archive)
            self.assertEqual(digest, hashlib.sha256(archive.read_bytes()).hexdigest())
            self.assertEqual(district_for_address("경기도 평택시 고덕동 1", districts)[0], "41220")
            self.assertEqual(district_for_address("서울시 종로구 청운동 1", districts)[0], "11110")
            self.assertEqual(district_for_address("경기도 성남수정구 고등동 1", districts)[0], "41173")
            self.assertEqual(district_for_address("경기도 없는시 1", districts), (None, None))

    def test_verified_response_rejects_wrong_district(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            payload = (b"<response><header><resultCode>000</resultCode></header>"
                       b"<body><items><item><sggCd>11140</sggCd><dealYear>2023</dealYear>"
                       b"<dealMonth>1</dealMonth></item></items><totalCount>1</totalCount>"
                       b"</body></response>")
            (folder / "page_0001.xml").write_bytes(payload)
            (folder / "rows.jsonl").write_text(json.dumps({
                "sggCd": "11140", "dealYear": "2023", "dealMonth": "1"
            }) + "\n", encoding="utf-8")
            (folder / "manifest.json").write_text(json.dumps({
                "filters": {"LAWD_CD": "11110", "DEAL_YMD": "202301"},
                "pages": [{"file": "page_0001.xml", "sha256": hashlib.sha256(payload).hexdigest(),
                           "rows": 1}],
                "row_count": 1,
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "mismatch"):
                verify_copy(folder, "11110", "202301")

    def test_legal_address_parts_handle_ri_and_attached_lot(self) -> None:
        self.assertEqual(
            _address_parts("경기도 김포시 통진읍 마송리 586", "경기도 김포시"),
            ("통진읍 마송리", "586"),
        )
        self.assertEqual(
            _address_parts("인천광역시 중구 중산동1871-1", "인천광역시 중구"),
            ("중산동", "1871-1"),
        )
        self.assertEqual(
            _address_parts("경기도 고양시 덕양구 대덕산로 20", "경기도 고양시 덕양구"),
            (None, None),
        )


if __name__ == "__main__":
    unittest.main()
