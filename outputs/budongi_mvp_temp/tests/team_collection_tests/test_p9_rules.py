import unittest

from budongi.team_collection import contract as C
from budongi.team_collection.profile.rules import compile_rule


class P9RulesVisibleTest(unittest.TestCase):
    def test_int_bounds(self):
        ge = compile_rule("int>=0")
        self.assertIs(ge("12"), True)
        self.assertIs(ge("0"), True)
        self.assertIs(ge("-1"), False)
        le = compile_rule("int<=10")
        self.assertIs(le("10"), True)
        self.assertIs(le("11"), False)

    def test_decimal(self):
        pred = compile_rule("decimal")
        self.assertIs(pred("3.14"), True)
        self.assertIs(pred("-3"), True)
        self.assertIs(pred("abc"), False)

    def test_range_inclusive(self):
        pred = compile_rule("range:-90..90")
        self.assertIs(pred("37.5665"), True)
        self.assertIs(pred("90"), True)
        self.assertIs(pred("-90"), True)
        self.assertIs(pred("90.1"), False)

    def test_regex_fullmatch(self):
        pred = compile_rule("regex:[0-9]{5}")
        self.assertIs(pred("12345"), True)
        self.assertIs(pred("123456"), False)

    def test_date(self):
        pred = compile_rule("date")
        self.assertIs(pred("2024-02-29"), True)
        self.assertIs(pred("2023-02-29"), False)

    def test_yyyymm(self):
        pred = compile_rule("yyyymm")
        self.assertIs(pred("202412"), True)
        self.assertIs(pred("202413"), False)

    def test_in_options(self):
        pred = compile_rule("in:Y|N")
        self.assertIs(pred("N"), True)
        self.assertIs(pred("y"), False)

    def test_len_rules(self):
        self.assertIs(compile_rule("len<=3")("abc"), True)
        self.assertIs(compile_rule("len<=3")("abcd"), False)
        self.assertIs(compile_rule("len==2")("ab"), True)
        self.assertIs(compile_rule("len==2")("a"), False)

    def test_conjunction(self):
        pred = compile_rule("len==5 & regex:[0-9]+")
        self.assertIs(pred("11010"), True)
        self.assertIs(pred("1101"), False)
        self.assertIs(pred("1101a"), False)

    def test_unknown_rule_raises(self):
        for text in ("nope", ""):
            with self.assertRaises(C.ContractError) as ctx:
                compile_rule(text)
            self.assertEqual(str(ctx.exception), "invalid_rule")


if __name__ == "__main__":
    unittest.main()
