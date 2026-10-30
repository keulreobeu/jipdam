import unittest

from budongi.team_collection import contract as C
from budongi.team_collection.base import RequestSpec
from budongi.team_collection.runtime.scheduler import Scheduler


def spec(rid):
    return RequestSpec(request_id=rid, lane="B", origin="https://example.test",
                       url_template="https://example.test/p")


class FakeClock:
    def __init__(self, t=0.0):
        self.t = t

    def __call__(self):
        return self.t


class SchedulerVisibleTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock(0.0)
        self.s = Scheduler(self.clock)

    def test_push_then_pop_ready(self):
        a = spec("a")
        self.s.push(a)
        self.assertIs(self.s.pop_ready(), a)
        self.assertIsNone(self.s.pop_ready())
        self.assertEqual(self.s.pending(), 1)

    def test_future_not_before_waits(self):
        a = spec("a")
        self.s.push(a, not_before=10)
        self.assertIsNone(self.s.pop_ready())
        self.assertEqual(self.s.next_wakeup(), 10)
        self.clock.t = 10
        self.assertIs(self.s.pop_ready(), a)

    def test_earliest_not_before_first(self):
        self.clock.t = 6
        a, b = spec("a"), spec("b")
        self.s.push(a, not_before=5)
        self.s.push(b, not_before=3)
        self.assertIs(self.s.pop_ready(), b)
        self.assertIs(self.s.pop_ready(), a)

    def test_ties_by_push_order(self):
        a, b = spec("a"), spec("b")
        self.s.push(b, not_before=0)
        self.s.push(a, not_before=0)
        self.assertEqual(self.s.pop_ready().request_id, "b")
        self.assertEqual(self.s.pop_ready().request_id, "a")

    def test_duplicate_request(self):
        self.s.push(spec("a"))
        with self.assertRaises(C.ContractError) as cm:
            self.s.push(spec("a"))
        self.assertEqual(str(cm.exception), "duplicate_request")
        self.assertEqual(self.s.pending(), 1)

    def test_defer_requeues(self):
        a = spec("a")
        self.s.push(a)
        self.assertIs(self.s.pop_ready(), a)
        self.s.defer(a, 20)
        self.assertIsNone(self.s.pop_ready())
        self.assertEqual(self.s.next_wakeup(), 20)
        self.clock.t = 20
        self.assertIs(self.s.pop_ready(), a)

    def test_done_and_pending(self):
        self.s.push(spec("a"))
        self.s.push(spec("b"))
        self.assertEqual(self.s.pending(), 2)
        self.assertEqual(self.s.pop_ready().request_id, "a")
        self.assertEqual(self.s.pending(), 2)
        self.s.done("a")
        self.assertEqual(self.s.pending(), 1)

    def test_done_requires_in_flight(self):
        self.s.push(spec("a"))
        with self.assertRaises(C.ContractError) as cm:
            self.s.done("a")
        self.assertEqual(str(cm.exception), "not_in_flight")

    def test_empty_scheduler(self):
        self.assertEqual(self.s.pending(), 0)
        self.assertIsNone(self.s.next_wakeup())
        self.assertIsNone(self.s.pop_ready())


if __name__ == "__main__":
    unittest.main()
