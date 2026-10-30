import unittest

from budongi.team_collection import contract as C
from budongi.team_collection.base import Verdict
from budongi.team_collection.runtime.classify import classify_datagokr, classify_seoul, classify_topis


class TestE6Datagokr(unittest.TestCase):
    def test_documented_table(self):
        table = {"00": "ok", "03": "empty", "22": "quota_daily", "23": "rate",
                 "01": "transient", "02": "transient", "04": "transient", "05": "transient",
                 "99": "transient",
                 "20": "auth", "21": "auth", "29": "auth", "30": "auth", "31": "auth",
                 "32": "auth", "33": "auth",
                 "10": "request_error", "11": "request_error", "12": "request_error"}
        for code, kind in table.items():
            self.assertEqual(classify_datagokr(code), Verdict(kind, code))

    def test_strip_and_fail_closed(self):
        self.assertEqual(classify_datagokr(" 00 "), Verdict("ok", "00"))
        for unknown in ("0", "000", "2", "OK", ""):
            self.assertEqual(classify_datagokr(unknown), Verdict("api_response_error", unknown))

    def test_non_str_raises(self):
        for bad in (None, 22, b"22", True):
            with self.assertRaises(C.ContractError) as cm:
                classify_datagokr(bad)
            self.assertEqual(str(cm.exception), "invalid_code")


class TestE6Seoul(unittest.TestCase):
    def test_exact_and_prefix_rules(self):
        self.assertEqual(classify_seoul("INFO-000"), Verdict("ok", "INFO-000"))
        self.assertEqual(classify_seoul("INFO-200"), Verdict("empty", "INFO-200"))
        self.assertEqual(classify_seoul("INFO-100"), Verdict("auth", "INFO-100"))
        self.assertEqual(classify_seoul("ERROR-300").kind, "request_error")
        self.assertEqual(classify_seoul("ERROR-336").kind, "request_error")
        self.assertEqual(classify_seoul("ERROR-500").kind, "transient")
        self.assertEqual(classify_seoul("ERROR-601").kind, "transient")

    def test_fail_closed_is_case_sensitive(self):
        for unknown in ("info-000", "INFO-300", "ERROR-400", ""):
            self.assertEqual(classify_seoul(unknown), Verdict("api_response_error", unknown))


class TestE6Topis(unittest.TestCase):
    def test_zero_is_ok_whatever_the_message(self):
        self.assertEqual(classify_topis("0", "정상적으로 처리되었습니다."), Verdict("ok", "0"))
        self.assertEqual(classify_topis(" 0 ", ""), Verdict("ok", "0"))

    def test_message_disambiguates_reused_codes(self):
        self.assertEqual(classify_topis("8", "운행 종료되었습니다"), Verdict("empty", "8"))
        self.assertEqual(classify_topis("8", "요청 제한을 초과하였습니다"), Verdict("quota_daily", "8"))
        self.assertEqual(classify_topis("4", "결과가 존재하지 않습니다"), Verdict("empty", "4"))
        self.assertEqual(classify_topis("4", "노선을 찾을 수 없습니다"), Verdict("request_error", "4"))
        self.assertEqual(classify_topis("7", "사용중지된 키입니다"), Verdict("auth", "7"))
        self.assertEqual(classify_topis("7", "경로 검색 결과가 존재하지 않습니다"), Verdict("empty", "7"))

    def test_message_table(self):
        for msg, kind in [("인증키 없음", "auth"), ("등록되지 않은 키", "auth"),
                          ("시스템 오류", "transient"), ("API서비스 준비중", "transient"),
                          ("실시간 정보를 읽을 수 없습니다", "transient"),
                          ("잘못된 쿼리 요청", "request_error"), ("필수 Parameter 없음", "request_error"),
                          ("노선번호는 1자리 이상", "request_error"),
                          ("정류소를 찾을 수 없습니다", "request_error")]:
            self.assertEqual(classify_topis("9", msg), Verdict(kind, "9"), msg)

    def test_fail_closed_and_types(self):
        self.assertEqual(classify_topis("5", "모르는 메시지"), Verdict("api_response_error", "5"))
        with self.assertRaises(C.ContractError) as cm:
            classify_topis("0", None)
        self.assertEqual(str(cm.exception), "invalid_code")


if __name__ == "__main__":
    unittest.main()
