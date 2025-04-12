import ast
from pathlib import Path
from unittest import TestCase

from abstracttree.generics import children, MappingItem, parent, label

SKIPTOKEN = "<skip>"
ERRTOKEN = "<error>"


class A: pass


class B(A): pass


class TestGenerics(TestCase):
    def setUp(self):
        self.cases = [
            [1, 2, 3],
            {"a": 1, "b": "hello", ("c", "d"): [4, 5, 6]},
            MappingItem("b", "hello"),
            MappingItem(("c", "d"), [4, 5, 6]),
            A,
            ast.parse("1 + a", mode="eval").body,
            Path(__file__).parent.parent / ".github"
        ]

    def test_children(self):

        expectations = [
            [1, 2, 3],
            list({"a": 1, "b": "hello", ("c", "d"): [4, 5, 6]}.items()),
            ["hello"],
            [4, 5, 6],
            [B],
            SKIPTOKEN, #[ast.parse("1", mode="eval").body, ast.parse("a", mode="eval").body],
            (Path(__file__).parent.parent / ".github/workflows",)
        ]

        for case, expected in zip(self.cases, expectations, strict=True):
            if expected is SKIPTOKEN:
                continue

            with self.subTest("Test for {case}"):
                self.assertEqual(expected, children(case))

    def test_parent(self):
        expectations = [
            ERRTOKEN,
            ERRTOKEN,
            ERRTOKEN,
            ERRTOKEN,
            ERRTOKEN,
            ERRTOKEN,
            Path(__file__).parent.parent,
        ]

        for case, expected in zip(self.cases, expectations, strict=True):
            with self.subTest("Test for {case}"):
                if expected is not ERRTOKEN:
                    self.assertEqual(expected, parent(case))
                else:
                    with self.assertRaises(TypeError):
                        parent(case)


    def test_label(self):
        expectations = [
            "list[3]",
            "dict[3]",
            "b",
            "('c', 'd')",
            "A",
            "BinOp(left=↓, op=Add(), right=↓)",
            ".github",
        ]

        for case, expected in zip(self.cases, expectations, strict=True):
            if expected is SKIPTOKEN:
                continue
            with self.subTest("Test for {case}"):
                self.assertEqual(expected, label(case))
