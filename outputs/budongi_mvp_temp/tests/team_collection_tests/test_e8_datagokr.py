import unittest

from budongi.team_collection import contract as C
from budongi.team_collection.adapters.datagokr import page_count, parse_page

JSON_OK = (b'{"response":{"header":{"resultCode":"00","resultMsg":"NORMAL SERVICE."},'
           b'"body":{"items":{"item":[{"sido":"\xec\x84\x9c\xec\x9a\xb8"},{"sido":"\xeb\xb6\x80\xec\x82\xb0"}]},'
           b'"numOfRows":10,"pageNo":1,"totalCount":253}}}')
JSON_EMPTY = (b'{"response":{"header":{"resultCode":"03","resultMsg":"NODATA_ERROR"},'
              b'"body":{"items":"","totalCount":0}}}')
JSON_SINGLE = (b'{"response":{"header":{"resultCode":"00"},'
               b'"body":{"items":{"item":{"only":"one"}},"totalCount":"1"}}}')
GATEWAY = (b'<OpenAPI_ServiceResponse><cmmMsgHeader><errMsg>SERVICE ERROR</errMsg>'
           b'<returnAuthMsg>LIMITED_NUMBER_OF_SERVICE_REQUESTS_EXCEEDS_ERROR</returnAuthMsg>'
           b'<returnReasonCode>22</returnReasonCode></cmmMsgHeader></OpenAPI_ServiceResponse>')
XML_OK = (b'<response><header><resultCode>00</resultCode><resultMsg>OK</resultMsg></header>'
          b'<body><items><item><sido>\xec\x84\x9c\xec\x9a\xb8</sido><cnt>3</cnt></item></items>'
          b'<numOfRows>10</numOfRows><totalCount>1</totalCount></body></response>')


class TestE8Json(unittest.TestCase):
    def test_item_list(self):
        page, code = parse_page(JSON_OK)
        self.assertEqual(code, "00")
        self.assertEqual(page.total, 253)
        self.assertEqual(page.status, "ok")
        self.assertEqual(page.rows, ({"sido": "서울"}, {"sido": "부산"}))

    def test_empty_items_string(self):
        page, code = parse_page(JSON_EMPTY)
        self.assertEqual((page.rows, page.total, page.status), ((), 0, "empty"))
        self.assertEqual(code, "03")

    def test_single_item_dict_and_digit_total(self):
        page, code = parse_page(JSON_SINGLE)
        self.assertEqual(page.rows, ({"only": "one"},))
        self.assertEqual(page.total, 1)

    def test_missing_body_is_empty(self):
        page, code = parse_page(b'{"response":{"header":{"resultCode":"30"}}}')
        self.assertEqual((page.rows, page.total, page.status), ((), None, "empty"))
        self.assertEqual(code, "30")

    def test_int_result_code_becomes_text(self):
        page, code = parse_page(b'{"response":{"header":{"resultCode":0}}}')
        self.assertEqual(code, "0")


class TestE8Xml(unittest.TestCase):
    def test_gateway_error(self):
        page, code = parse_page(GATEWAY)
        self.assertEqual((page.rows, page.total, page.status), ((), None, "empty"))
        self.assertEqual(code, "22")

    def test_body_items(self):
        page, code = parse_page(XML_OK)
        self.assertEqual(code, "00")
        self.assertEqual(page.rows, ({"sido": "서울", "cnt": "3"},))
        self.assertEqual(page.total, 1)
        self.assertEqual(page.status, "ok")

    def test_leading_whitespace_and_declaration(self):
        page, code = parse_page(b"  \r\n" + XML_OK)
        self.assertEqual(code, "00")
        page, code = parse_page(b'<?xml version="1.0" encoding="UTF-8"?>' + XML_OK)
        self.assertEqual(code, "00")


class TestE8Errors(unittest.TestCase):
    def test_invalid_payloads(self):
        cases = [b"", b"   ", b"plain text", b"[1]", b"<other/>",
                 b"<response><body/></response>",
                 b'{"response":{"header":{}}}',
                 b'{"response":{"header":{"resultCode":"00"},"body":{"items":{"item":[1]}}}}',
                 b'{"response":{"header":{"resultCode":"00"},"body":{"totalCount":-1}}}',
                 b"<response><header><resultCode>00</resultCode></header><body>"
                 b"<totalCount>x1</totalCount></body></response>"]
        for raw in cases:
            with self.assertRaises(C.ContractError, msg=raw) as cm:
                parse_page(raw)
            self.assertEqual(str(cm.exception), "invalid_payload", raw)
        with self.assertRaises(C.ContractError) as cm:
            parse_page(b"{\xff}")
        self.assertEqual(str(cm.exception), "decode_error")


class TestE8Pages(unittest.TestCase):
    def test_ceiling_and_zero(self):
        self.assertEqual(page_count(253, rows=100), 3)
        self.assertEqual(page_count(300, rows=100), 3)
        self.assertEqual(page_count(0, rows=100), 0)
        self.assertEqual(page_count(1, rows=100), 1)

    def test_argument_checks(self):
        with self.assertRaises(C.ContractError) as cm:
            page_count(-1, rows=10)
        self.assertEqual(str(cm.exception), "invalid_total")
        with self.assertRaises(C.ContractError) as cm:
            page_count(10, rows=0)
        self.assertEqual(str(cm.exception), "invalid_rows")
        with self.assertRaises(C.ContractError) as cm:
            page_count(True, rows=10)
        self.assertEqual(str(cm.exception), "invalid_total")


if __name__ == "__main__":
    unittest.main()
