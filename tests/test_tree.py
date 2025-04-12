from unittest import TestCase

import tree_instances as trees


class TestTree(TestCase):
    def test_siblings_iter(self):
        tree = trees.INFINITE_BINARY_TREE
        values = [node.value for node in tree.siblings]
        values_left = [node.value for node in tree.children[0].siblings]
        values_right = [node.value for node in tree.children[1].siblings]
        values_lr = [node.value for node in tree.children[0].children[1].siblings]
        self.assertEqual([], values)
        self.assertEqual([2], values_left)
        self.assertEqual([1], values_right)
        self.assertEqual([3], values_lr)

    def test_siblings_count(self):
        self.assertEqual(0, trees.SINGLETON.siblings.count())
        self.assertEqual(-1, trees.NONEXISTENTPATH.siblings.count())
        self.assertEqual(0, trees.INFINITE_BINARY_TREE.siblings.count())
        self.assertEqual(1, trees.INFINITE_BINARY_TREE_SUBTREE.siblings.count())
        self.assertEqual(0, trees.COUNTDOWN.siblings.count())
        self.assertEqual(0, trees.COUNTDOWN.root.siblings.count())
        self.assertEqual(0, trees.INFINITE_TREE.siblings.count())
