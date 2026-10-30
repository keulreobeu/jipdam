import unittest

from budongi.team_collection import contract as C
from budongi.team_collection.adapters.topis import parse_page

OK = ("<ServiceResult><comMsgHeader/><msgHeader><headerCd>0</headerCd>"
      "<headerMsg>정상적으로 처리되었습니다.</headerMsg><itemCount>0</itemCount></msgHeader>"
      "<msgBody><itemList><busRouteId>100100112</busRouteId><busRouteNm>1225</busRouteNm>"
      "<routeType>3</routeType></itemList>"
      "<itemList><busRouteId>100100001</busRouteId><busRouteNm>01A</busRouteNm>"
      "<routeType>5</routeType></itemList></msgBody></ServiceResult>").encode("utf-8")
NO_RESULT = ("<ServiceResult><msgHeader><headerCd>4</headerCd>"
             "<headerMsg>결과가 존재하지 않습니다.</headerMsg></msgHeader></ServiceResult>").encode("utf-8")
GATEWAY = (b"<OpenAPI_ServiceResponse><cmmMsgHeader>"
           b"<returnAuthMsg>LIMITED_NUMBER_OF_SERVICE_REQUESTS_EXCEEDS_ERROR</returnAuthMsg>"
           b"<returnReasonCode>22</returnReasonCode></cmmMsgHeader></OpenAPI_ServiceResponse>")


class TestE9Topis(unittest.TestCase):
    def test_rows_in_document_order(self):
        page, cd, msg = parse_page(OK)
        self.assertEqual(cd, "0")
        self.assertEqual(msg, "정상적으로 처리되었습니다.")
        self.assertEqual(page.total, None)
        self.assertEqual(page.status, "ok")
        self.assertEqual(page.rows,
                         ({"busRouteId": "100100112", "busRouteNm": "1225", "routeType": "3"},
                          {"busRouteId": "100100001", "busRouteNm": "01A", "routeType": "5"}))

    def test_no_body_is_empty(self):
        page, cd, msg = parse_page(NO_RESULT)
        self.assertEqual((page.rows, page.total, page.status), ((), None, "empty"))
        self.assertEqual((cd, msg), ("4", "결과가 존재하지 않습니다."))

    def test_gateway_error(self):
        page, cd, msg = parse_page(GATEWAY)
        self.assertEqual((page.rows, page.total, page.status), ((), None, "empty"))
        self.assertEqual(cd, "22")
        self.assertEqual(msg, "LIMITED_NUMBER_OF_SERVICE_REQUESTS_EXCEEDS_ERROR")

    def test_missing_header_msg_is_blank(self):
        page, cd, msg = parse_page(b"<ServiceResult><msgHeader><headerCd>1</headerCd>"
                                   b"</msgHeader></ServiceResult>")
        self.assertEqual((cd, msg), ("1", ""))

    def test_invalid_payloads(self):
        for raw in (b"not xml", b"<html></html>",
                    b"<ServiceResult><msgHeader></msgHeader></ServiceResult>",
                    b"<ServiceResult><msgHeader><headerCd> </headerCd></msgHeader></ServiceResult>",
                    b"<OpenAPI_ServiceResponse><cmmMsgHeader/></OpenAPI_ServiceResponse>"):
            with self.assertRaises(C.ContractError, msg=raw) as cm:
                parse_page(raw)
            self.assertEqual(str(cm.exception), "invalid_payload", raw)
        with self.assertRaises(C.ContractError) as cm:
            parse_page("<ServiceResult/>")
        self.assertEqual(str(cm.exception), "invalid_payload")


if __name__ == "__main__":
    unittest.main()
