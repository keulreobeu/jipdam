import unittest

from budongi.team_collection.core.missing import (
    SEMANTIC_TOKENS,
    classify_value,
    is_placeholder_phone,
)


class TestC3SemanticTokens(unittest.TestCase):
    def test_tokens_exact(self):
        self.assertIsInstance(SEMANTIC_TOKENS, frozenset)
        self.assertEqual(SEMANTIC_TOKENS, frozenset({"", "-", "미상", "0000", "99991231"}))
        for text in SEMANTIC_TOKENS:
            self.assertEqual(classify_value(text), "semantic", text)


class TestC3ClassifyValue(unittest.TestCase):
    def test_none_is_null(self):
        self.assertEqual(classify_value(None), "null")

    def test_tokens_are_semantic(self):
        for text in ("", "-", "미상", "0000", "99991231"):
            self.assertEqual(classify_value(text), "semantic", text)

    def test_stripped_token_is_semantic(self):
        self.assertEqual(classify_value("  미상 "), "semantic")
        self.assertEqual(classify_value("   "), "semantic")

    def test_plain_text_is_present(self):
        self.assertEqual(classify_value("서울역"), "present")
        self.assertEqual(classify_value("12"), "present")

    def test_zero_number_is_present(self):
        self.assertEqual(classify_value(0), "present")
        self.assertEqual(classify_value(1.5), "present")

    def test_extra_tokens(self):
        self.assertEqual(classify_value("N/A", extra=frozenset({"N/A"})), "semantic")
        self.assertEqual(classify_value("ok", extra=frozenset({"N/A"})), "present")

    def test_phone_placeholder_kind(self):
        self.assertEqual(classify_value("02-0000-0000", kind="phone"), "semantic")
        self.assertEqual(classify_value("02-1234-5678", kind="phone"), "present")

    def test_placeholder_without_phone_kind_present(self):
        self.assertEqual(classify_value("02-0000-0000"), "present")


class TestC3PlaceholderPhone(unittest.TestCase):
    def test_area_code_placeholders(self):
        self.assertIs(is_placeholder_phone("02-0000-0000"), True)
        self.assertIs(is_placeholder_phone("031-000-0000"), True)

    def test_separators_removed(self):
        self.assertIs(is_placeholder_phone("(02) 000-0000"), True)
        self.assertIs(is_placeholder_phone("010.0000.0000"), True)

    def test_all_zeros(self):
        self.assertIs(is_placeholder_phone("000-0000"), True)

    def test_real_number_false(self):
        self.assertIs(is_placeholder_phone("02-1234-5678"), False)

    def test_too_short_false(self):
        self.assertIs(is_placeholder_phone("000000"), False)


if __name__ == "__main__":
    unittest.main()
