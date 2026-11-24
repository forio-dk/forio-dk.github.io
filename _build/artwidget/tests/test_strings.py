import unittest

from strings import load_strings, shape_errors


class ShapeTest(unittest.TestCase):
    def test_same_shape(self):
        self.assertEqual(shape_errors({"a": 1, "b": [{"x": "s"}]}, {"a": 2, "b": [{"x": "t"}]}), [])

    def test_missing(self):
        self.assertEqual(shape_errors({"a": "", "b": ""}, {"a": ""}), ["b: missing"])

    def test_unexpected(self):
        self.assertEqual(shape_errors({"a": ""}, {"a": "", "c": ""}), ["c: unexpected"])

    def test_list_length(self):
        self.assertEqual(shape_errors({"b": ["", "", ""]}, {"b": ["", ""]}), ["b: 2 items, expected 3"])

    def test_type(self):
        self.assertEqual(shape_errors({"a": ""}, {"a": []}), ["a: list, expected str"])

    def test_nested_path(self):
        self.assertEqual(shape_errors({"m": {"t": ""}}, {"m": {}}), ["m.t: missing"])

    def test_english_loads(self):
        en = load_strings(["en"])["en"]
        self.assertEqual(en["meta"]["title"], "Art Widget: Artwork of the Day")
        self.assertEqual(len(en["how"]["steps"]), 3)
        self.assertEqual(len(en["features"]["items"]), 6)
