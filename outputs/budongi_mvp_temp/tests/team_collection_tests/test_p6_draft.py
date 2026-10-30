import unittest

from budongi.team_collection import contract as C
from budongi.team_collection.issues.draft import (
    FIELD_IDS,
    ISSUE_FORM_URL,
    QUALITY_OPTIONS,
    STATUS_OPTIONS,
    issue_title,
    prefill_url,
    render_issue,
)

Q0 = "실제 / 원천 미검수"
RES = {"source": "S", "scope": "R", "method": "M", "quality": Q0, "duplicates": "D"}
RES_BODY = (
    "### 출처·데이터 종류\n\nS\n\n### 범위·담당자\n\nR\n\n### 상태·결과\n\n상태: 예약\n\n미수집\n\n"
    "### 방법·품질\n\n방법: M\n\n검수 구분: 실제 / 원천 미검수\n\n### 중복 확인·재개\n\nD\n\n"
    "### 파일·해시·manifest\n\n미생성\n\n### Drive 파일\n\n업로드 대기\n"
)


class TestP6Constants(unittest.TestCase):
    def test_form_url_and_ids(self):
        self.assertEqual(ISSUE_FORM_URL,
                         "https://github.com/keulreobeu/jipdam/issues/new?template=data-collection.yml")
        self.assertEqual(FIELD_IDS, ("source", "scope", "status", "results", "method", "quality",
                                     "duplicates", "artifact", "drive"))

    def test_options(self):
        self.assertEqual(STATUS_OPTIONS[0], "예약")
        self.assertEqual(len(STATUS_OPTIONS), 6)
        self.assertEqual(QUALITY_OPTIONS[0], Q0)
        self.assertEqual(len(QUALITY_OPTIONS), 3)


class TestP6Title(unittest.TestCase):
    def test_title_stripped(self):
        self.assertEqual(issue_title(source=" 서울 ", kind="버스정류소", region="서울", period="202610"),
                         "[수집] 서울 | 버스정류소 | 서울 | 202610")

    def test_title_pipe_rejected(self):
        with self.assertRaises(C.ContractError) as cm:
            issue_title(source="a|b", kind="k", region="r", period="p")
        self.assertEqual(str(cm.exception), "invalid_title_part")


class TestP6Render(unittest.TestCase):
    def test_reservation_body(self):
        self.assertEqual(render_issue("reservation", dict(RES)), RES_BODY)

    def test_result_body(self):
        data = dict(RES, status="업로드 완료", results="성공 25구\n총 10건", artifact="b-20261029-v1",
                    drive="https://drive.example/x")
        body = render_issue("result", data)
        self.assertIn("### 상태·결과\n\n상태: 업로드 완료\n\n성공 25구\n총 10건\n\n### 방법·품질", body)
        self.assertIn("### 파일·해시·manifest\n\nb-20261029-v1\n\n### Drive 파일\n\nhttps://drive.example/x\n",
                      body)
        self.assertTrue(body.endswith("x\n"))

    def test_reservation_forbids_drive(self):
        with self.assertRaises(C.ContractError) as cm:
            render_issue("reservation", dict(RES, drive="x"))
        self.assertEqual(str(cm.exception), "reservation_field_not_allowed:drive")

    def test_invalid_stage(self):
        with self.assertRaises(C.ContractError) as cm:
            render_issue("draft", {})
        self.assertEqual(str(cm.exception), "invalid_stage")


class TestP6Prefill(unittest.TestCase):
    def test_prefill_order_and_encoding(self):
        url = prefill_url({"status": "예약", "source": "a b"}, title="[수집] x")
        self.assertEqual(url, ISSUE_FORM_URL
                         + "&title=%5B%EC%88%98%EC%A7%91%5D%20x&source=a%20b&status=%EC%98%88%EC%95%BD")

    def test_prefill_rejects_handle(self):
        with self.assertRaises(C.ContractError) as cm:
            prefill_url({"scope": "서울 · @cannedJean"})
        self.assertEqual(str(cm.exception), "personal_data_in_url")

    def test_prefill_unknown_field(self):
        with self.assertRaises(C.ContractError) as cm:
            prefill_url({"owner": "x"})
        self.assertEqual(str(cm.exception), "unknown_field:owner")


if __name__ == "__main__":
    unittest.main()
