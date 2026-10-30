import unittest

from budongi.team_collection.issues.overlap import (SEOUL_WIDE, find_overlaps, parse_issue,
                                                     parse_period)

BODY = ("### 출처·데이터 종류\n\n국토교통부 실거래가\n\n"
        "### 상태\n\n예약\n\n"
        "### 데이터 검수 구분\n\n실제 / 원천 미검수\n")


def issue(number=7, title="[수집] 국토교통부 | 아파트 전월세 | 서울 전체 | 202401~202608",
          body=BODY, state="open", is_pr=False):
    return {"number": number, "title": title, "state": state, "body": body, "is_pr": is_pr}


def plan(**kw):
    base = {"source": "국토교통부", "kind": "아파트 전월세", "regions": ["강남구"],
            "period_start": "202501", "period_end": "202512"}
    base.update(kw)
    return base


class OverlapVisibleTests(unittest.TestCase):
    def test_seoul_wide_constant(self):
        self.assertEqual(SEOUL_WIDE, frozenset({"서울", "서울전체", "서울특별시", "서울시", "서울25구", "11"}))

    def test_parse_period_range_and_single(self):
        self.assertEqual(parse_period("202401~202608"), ("202401", "202608"))
        self.assertEqual(parse_period("2025-03"), ("202503", "202503"))
        self.assertEqual(parse_period("2024 ~ 2025.06"), ("202401", "202506"))

    def test_parse_period_reversed_is_none(self):
        self.assertIsNone(parse_period("202608~202401"))
        self.assertEqual(parse_period("202401~202401"), ("202401", "202401"))

    def test_parse_issue_fields(self):
        p = parse_issue(issue())
        self.assertEqual(p["number"], 7)
        self.assertTrue(p["is_collection"])
        self.assertEqual(p["source"], "국토교통부")
        self.assertEqual(p["kind"], "아파트 전월세")
        self.assertEqual(p["region"], "서울 전체")
        self.assertEqual(p["regions"], ("서울전체",))
        self.assertTrue(p["seoul_wide"])
        self.assertEqual((p["period_start"], p["period_end"]), ("202401", "202608"))
        self.assertEqual(p["status"], "예약")
        self.assertFalse(p["synthetic"])
        self.assertEqual(p["sections"]["출처·데이터 종류"], "국토교통부 실거래가")

    def test_parse_issue_key_set(self):
        keys = {"number", "title", "state", "is_pr", "is_collection", "source", "kind", "region",
                "period", "regions", "seoul_wide", "period_start", "period_end", "sections",
                "status", "synthetic"}
        self.assertEqual(set(parse_issue(issue())), keys)

    def test_find_overlaps_hit(self):
        hits = find_overlaps(plan(), [issue()])
        self.assertEqual(len(hits), 1)
        hit = hits[0]
        self.assertEqual(set(hit), {"number", "title", "state", "status", "blocking",
                                    "undetermined", "period_overlap"})
        self.assertEqual(hit["number"], 7)
        self.assertEqual(hit["state"], "open")
        self.assertEqual(hit["status"], "예약")
        self.assertTrue(hit["blocking"])
        self.assertEqual(hit["undetermined"], [])
        self.assertEqual(hit["period_overlap"], ("202501", "202512"))

    def test_find_overlaps_disjoint_period(self):
        self.assertEqual(find_overlaps(plan(period_start="202609", period_end="202610"), [issue()]), [])

    def test_find_overlaps_other_kind(self):
        self.assertEqual(find_overlaps(plan(kind="지하철역"), [issue()]), [])

    def test_find_overlaps_sorted(self):
        hits = find_overlaps(plan(), [issue(number=9), issue(number=3)])
        self.assertEqual([h["number"] for h in hits], [3, 9])

    def test_find_overlaps_empty(self):
        self.assertEqual(find_overlaps(plan(), []), [])


if __name__ == "__main__":
    unittest.main()
