from unittest import TestCase

import tree_instances as trees


class TestTree(TestCase):
    def test_siblings(self):
        self.assertEqual(0, trees.SINGLETON.siblings.count())
        self.assertEqual(-1, trees.NONEXISTENTPATH.siblings.count())
        self.assertEqual(0, trees.INFINITE_BINARY_TREE.siblings.count())
        self.assertEqual(1, trees.INFINITE_BINARY_TREE_SUBTREE.siblings.count())
        self.assertEqual(0, trees.COUNTDOWN.siblings.count())
        self.assertEqual(0, trees.COUNTDOWN.root.siblings.count())
        self.assertEqual(0, trees.INFINITE_TREE.siblings.count())
