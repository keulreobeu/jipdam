import unittest

from budongi.team_collection import contract as C
from budongi.team_collection.runtime.ratelimit import Aimd, TokenBucket


class _FakeTime:
    def __init__(self, start=0.0, advance=True):
        self.now = start
        self.advance = advance
        self.sleeps = []

    def clock(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        if self.advance:
            self.now += seconds


class TestE5TokenBucketTypical(unittest.TestCase):
    def test_burst_then_wait(self):
        t = _FakeTime()
        b = TokenBucket(1.0, 2, clock=t.clock, sleep=t.sleep)
        self.assertEqual(b.acquire(), 0.0)
        self.assertEqual(b.acquire(), 0.0)
        self.assertEqual(t.sleeps, [])
        w = b.acquire()
        self.assertIsInstance(w, float)
        self.assertAlmostEqual(w, 1.0)
        self.assertEqual(len(t.sleeps), 1)
        self.assertAlmostEqual(t.sleeps[0], 1.0)

    def test_partial_refill_shortens_wait(self):
        t = _FakeTime()
        b = TokenBucket(2.0, 1, clock=t.clock, sleep=t.sleep)
        self.assertEqual(b.acquire(), 0.0)
        t.now += 0.25
        self.assertAlmostEqual(b.acquire(), 0.25)
        self.assertEqual(len(t.sleeps), 1)

    def test_full_refill_no_sleep(self):
        t = _FakeTime()
        b = TokenBucket(1.0, 1, clock=t.clock, sleep=t.sleep)
        b.acquire()
        t.now += 1.0
        self.assertEqual(b.acquire(), 0.0)
        self.assertEqual(t.sleeps, [])

    def test_invalid_rate_and_burst(self):
        t = _FakeTime()
        with self.assertRaises(C.ContractError) as cm:
            TokenBucket(0, 1, clock=t.clock, sleep=t.sleep)
        self.assertEqual(str(cm.exception), "invalid_rate")
        with self.assertRaises(C.ContractError) as cm:
            TokenBucket(1.0, 0, clock=t.clock, sleep=t.sleep)
        self.assertEqual(str(cm.exception), "invalid_burst")


class TestE5AimdTypical(unittest.TestCase):
    def test_start_rate(self):
        a = Aimd(10, 1, 20)
        self.assertIsInstance(a.rate, float)
        self.assertEqual(a.rate, 10.0)

    def test_additive_increase(self):
        a = Aimd(10, 1, 20, increase_after=2, step=1)
        self.assertEqual(a.success(), 10.0)
        self.assertEqual(a.success(), 11.0)
        self.assertEqual(a.rate, 11.0)

    def test_multiplicative_decrease(self):
        a = Aimd(10, 1, 20, increase_after=2, step=1)
        a.success()
        a.success()
        self.assertEqual(a.failure(), 5.5)
        self.assertEqual(a.rate, 5.5)

    def test_invalid_order(self):
        with self.assertRaises(C.ContractError) as cm:
            Aimd(5, 6, 10)
        self.assertEqual(str(cm.exception), "invalid_aimd")


if __name__ == "__main__":
    unittest.main()
