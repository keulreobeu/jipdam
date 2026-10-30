import json
import unittest

from budongi.team_collection import contract as C
from budongi.team_collection.adapters.seoul import parse_page, window_params

OK = {"busStopLocationXyInfo": {"list_total_count": 11236,
                                "RESULT": {"CODE": "INFO-000", "MESSAGE": "정상 처리되었습니다"},
                                "row": [{"STOPS_NO": "123000689", "XCRD": "127.084778"},
                                        {"STOPS_NO": "104000315", "XCRD": None}]}}
EMPTY = {"RESULT": {"CODE": "INFO-200", "MESSAGE": "해당하는 데이터가 없습니다."}}


def payload(doc):
    return json.dumps(doc, ensure_ascii=False).encode("utf-8")


class TestE7Parse(unittest.TestCase):
    def test_success_page(self):
        page, code = parse_page(payload(OK), service="busStopLocationXyInfo")
        self.assertEqual(code, "INFO-000")
        self.assertEqual(page.total, 11236)
        self.assertEqual(page.status, "ok")
        self.assertIsInstance(page.rows, tuple)
        self.assertEqual(page.rows[0], {"STOPS_NO": "123000689", "XCRD": "127.084778"})
        self.assertIsNone(page.rows[1]["XCRD"])

    def test_error_page_has_no_rows(self):
        page, code = parse_page(payload(EMPTY), service="busStopLocationXyInfo")
        self.assertEqual((page.rows, page.total, page.status), ((), None, "empty"))
        self.assertEqual(code, "INFO-200")

    def test_no_row_key_means_empty(self):
        doc = {"svc": {"list_total_count": 0, "RESULT": {"CODE": "INFO-000", "MESSAGE": "m"}}}
        page, code = parse_page(payload(doc), service="svc")
        self.assertEqual((page.rows, page.total, page.status), ((), 0, "empty"))

    def test_contract_errors(self):
        cases = [(b"\xec\x95", "decode_error"),                      # truncated UTF-8
                 (b"<html>", "invalid_payload"),
                 (b"[1, 2]", "invalid_payload"),
                 (payload({"other": {}}), "invalid_payload"),        # neither service nor RESULT
                 (payload({"svc": {"row": []}}), "invalid_payload"),  # RESULT missing
                 (payload({"svc": {"RESULT": {"CODE": "INFO-000"}, "row": [1]}}), "invalid_payload"),
                 (payload({"svc": {"RESULT": {"CODE": "INFO-000"}, "list_total_count": "3"}}),
                  "invalid_payload")]
        for raw, expected in cases:
            with self.assertRaises(C.ContractError, msg=raw) as cm:
                parse_page(raw, service="svc")
            self.assertEqual(str(cm.exception), expected)

    def test_payload_and_service_types(self):
        with self.assertRaises(C.ContractError) as cm:
            parse_page("{}", service="svc")
        self.assertEqual(str(cm.exception), "invalid_payload")
        with self.assertRaises(C.ContractError) as cm:
            parse_page(b"{}", service="")
        self.assertEqual(str(cm.exception), "invalid_service")


class TestE7Windows(unittest.TestCase):
    def test_windows_cover_total_exactly(self):
        self.assertEqual(window_params(2500), ((1, 1000), (1001, 2000), (2001, 2500)))
        self.assertEqual(window_params(1000), ((1, 1000),))
        self.assertEqual(window_params(1, size=5), ((1, 1),))
        self.assertEqual(window_params(0), ())

    def test_argument_checks(self):
        with self.assertRaises(C.ContractError) as cm:
            window_params(-1)
        self.assertEqual(str(cm.exception), "invalid_total")
        with self.assertRaises(C.ContractError) as cm:
            window_params(10, size=1001)
        self.assertEqual(str(cm.exception), "invalid_size")
        with self.assertRaises(C.ContractError) as cm:
            window_params(True)
        self.assertEqual(str(cm.exception), "invalid_total")


if __name__ == "__main__":
    unittest.main()
