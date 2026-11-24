import unittest

from plural import CATEGORIES, plural_category


class PluralTest(unittest.TestCase):
    def check(self, code: str, expected: dict[int, str]) -> None:
        self.assertEqual({n: plural_category(code, n) for n in expected}, expected)

    def test_english_danish_italian(self):
        for code in ("en", "da", "it"):
            with self.subTest(code=code):
                self.check(code, {0: "other", 1: "one", 2: "other", 15: "other", 21: "other"})

    def test_romanian(self):
        # one: 1; few: 0 and numbers ending in 01-19 (other than 1); other: the rest, which take "de" (20 de ...)
        self.check("ro", {0: "few", 1: "one", 2: "few", 15: "few", 19: "few", 20: "other", 21: "other", 101: "few",
                          120: "other"})

    def test_russian_ukrainian(self):
        for code in ("ru", "uk"):
            with self.subTest(code=code):
                self.check(code, {0: "many", 1: "one", 2: "few", 4: "few", 5: "many", 11: "many", 12: "many",
                                  15: "many", 21: "one", 22: "few", 25: "many", 111: "many", 112: "many"})

    def test_categories(self):
        self.assertEqual(CATEGORIES, ("one", "few", "many", "other"))

    def test_unknown_language(self):
        with self.assertRaises(KeyError):
            plural_category("xx", 1)
