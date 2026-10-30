import unittest

from budongi.team_collection import contract as C
from budongi.team_collection.adapters.filedata import (datagokr_detail_downloads, datagokr_file_url,
                                                       kric_file_url, seoul_file_url,
                                                       standard_page_params)

HTML = """<div onclick="fn_fileDataDown('uddi:p1','uddi:d1','FILE_000000002698621','1','CSV')">csv</div>
<a href="#" onclick="fn_fileDataDown( 'uddi:p1' , 'uddi:d1' , 'FILE_000000002698621' , '2' , 'XLSX' )">x</a>
<span>fn_fileDataDown('uddi:p1','uddi:d1','FILE_000000002698621','1','CSV')</span>"""

COLUMN_DOC = {"totalCount": 18343,
              "tableVO": {"svcTableNm": "TB_PARK", "colNmList": ["A", "B", "C"], "limit": 50000}}


class TestE10Urls(unittest.TestCase):
    def test_seoul_file_url_literal_order(self):
        self.assertEqual(seoul_file_url("OA-15636", inf_seq=1, seq="99"),
                         "https://datafile.seoul.go.kr/bigfile/iot/inf/nio_download.do"
                         "?&useCache=false&infId=OA-15636&seqNo=&seq=99&infSeq=1")

    def test_seoul_file_url_checks(self):
        with self.assertRaises(C.ContractError) as cm:
            seoul_file_url("15636", inf_seq=1, seq=1)
        self.assertEqual(str(cm.exception), "invalid_dataset_id")
        with self.assertRaises(C.ContractError) as cm:
            seoul_file_url("OA-15636", inf_seq=1, seq="9a")
        self.assertEqual(str(cm.exception), "invalid_file_param")
        with self.assertRaises(C.ContractError) as cm:
            seoul_file_url("OA-15636", inf_seq=True, seq=1)
        self.assertEqual(str(cm.exception), "invalid_file_param")

    def test_datagokr_file_url(self):
        self.assertEqual(datagokr_file_url("FILE_000000002698621", 1),
                         "https://www.data.go.kr/cmm/cmm/fileDownload.do"
                         "?atchFileId=FILE_000000002698621&fileDetailSn=1&insertDataPrcus=N")
        with self.assertRaises(C.ContractError) as cm:
            datagokr_file_url("FILE_bad!", 1)
        self.assertEqual(str(cm.exception), "invalid_file_id")

    def test_kric_file_url(self):
        self.assertEqual(kric_file_url(32, "1"),
                         "https://data.kric.go.kr/rips/dataset/download.file"
                         "?type=filedata&id=32&operation=1")


class TestE10DetailParse(unittest.TestCase):
    def test_finds_and_deduplicates_in_order(self):
        self.assertEqual(datagokr_detail_downloads(HTML),
                         ({"atch_file_id": "FILE_000000002698621", "file_detail_sn": "1", "ext": "csv"},
                          {"atch_file_id": "FILE_000000002698621", "file_detail_sn": "2", "ext": "xlsx"}))

    def test_no_match_and_bad_type(self):
        self.assertEqual(datagokr_detail_downloads("<html></html>"), ())
        with self.assertRaises(C.ContractError) as cm:
            datagokr_detail_downloads(b"bytes")
        self.assertEqual(str(cm.exception), "invalid_payload")


class TestE10StandardPages(unittest.TestCase):
    def test_pages_and_param_order(self):
        pages = standard_page_params(COLUMN_DOC, public_data_pk="15012890")
        self.assertEqual(len(pages), 2)
        self.assertEqual(pages[0],
                         (("publicDataPk", "15012890"), ("colNmList", "A"), ("colNmList", "B"),
                          ("colNmList", "C"), ("totalCount", "18343"), ("svcTableNm", "TB_PARK"),
                          ("perPage", "10000"), ("page", "1")))
        self.assertEqual(pages[1][-1], ("page", "2"))

    def test_zero_rows_no_pages(self):
        doc = {"totalCount": 0, "tableVO": {"svcTableNm": "T", "colNmList": ["A"], "limit": 50000}}
        self.assertEqual(standard_page_params(doc, public_data_pk="x"), ())

    def test_over_limit_refused(self):
        doc = {"totalCount": 50001, "tableVO": {"svcTableNm": "T", "colNmList": ["A"], "limit": 50000}}
        with self.assertRaises(C.ContractError) as cm:
            standard_page_params(doc, public_data_pk="x")
        self.assertEqual(str(cm.exception), "standard_over_grid_limit")

    def test_shape_checks(self):
        bad = [{"totalCount": "1", "tableVO": {"svcTableNm": "T", "colNmList": ["A"], "limit": 1}},
               {"totalCount": 1, "tableVO": {"svcTableNm": "", "colNmList": ["A"], "limit": 1}},
               {"totalCount": 1, "tableVO": {"svcTableNm": "T", "colNmList": [], "limit": 1}},
               {"totalCount": 1}]
        for doc in bad:
            with self.assertRaises(C.ContractError, msg=doc) as cm:
                standard_page_params(doc, public_data_pk="x")
            self.assertEqual(str(cm.exception), "invalid_column_doc")
        with self.assertRaises(C.ContractError) as cm:
            standard_page_params(COLUMN_DOC, public_data_pk="bad pk")
        self.assertEqual(str(cm.exception), "invalid_file_param")
        with self.assertRaises(C.ContractError) as cm:
            standard_page_params(COLUMN_DOC, public_data_pk="x", per_page=10001)
        self.assertEqual(str(cm.exception), "invalid_file_param")


if __name__ == "__main__":
    unittest.main()
