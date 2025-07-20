import ast
from unittest import TestCase

from abstracttree import HeapTree, as_tree
from abstracttree.generics import TreeLike, DownTreeLike
from pathlib import Path, PurePath

try:
    ExceptionGroup
except NameError:
    # Patch this test for lower python versions
    class ExceptionGroup():
        def __init__(self, *args): ...

        @property
        def children(self): return []


class TreeLikeTest(TestCase):
    def setUp(self):
        self.treelike_instances = [
            Path("/HasParent/HasChildren"),
            HeapTree(list(range(40)), 5),
            as_tree(ast.parse("f(x, y) + b")),
        ]
        self.pure_downtreelike_instances = [
            [],
            ast.parse("f(x, y) + b"),
            ExceptionGroup("A lot of things went wrong today",
                           [ValueError("value"), IndexError("index")]),
        ]
        self.untreelike_instances = [
            PurePath("/HasParent/HasNoChildren"),
            3,
            "hello",
            False,
            None,
        ]

    def test_treelike(self):
        for inst in self.treelike_instances:
            with self.subTest(msg=str(inst)):
                self.assertIsInstance(inst, TreeLike)
                self.assertIsInstance(inst, DownTreeLike)

    def test_downtreelike(self):
        for inst in self.pure_downtreelike_instances:
            with self.subTest(msg=str(inst)):
                self.assertIsInstance(inst, DownTreeLike)
                self.assertNotIsInstance(inst, TreeLike)

    def test_untreelike(self):
        for inst in self.untreelike_instances:
            with self.subTest(msg=str(inst)):
                self.assertNotIsInstance(inst, DownTreeLike)
                self.assertNotIsInstance(inst, TreeLike)
