from unittest import TestCase

import tree_instances as trees


class TestDownTree(TestCase):
    def test_is_leaf(self):
        # Pycharm does not seem to support subtests
        # for case in [
        #     {"expected": True, "instance": trees.SINGLETON},
        #     {"expected": True, "instance": trees.NONEXISTENTPATH},
        #     {"expected": False, "instance": trees.BINARY_TREE},#
        #     {"expected": True, "instance": trees.BINARY_TREE_SUBTREE},
        #     {"expected": True, "instance": trees.COUNTDOWN},
        #     {"expected": False, "instance": trees.SEQTREE},
        # ]:
        #     with self.subTest(**case):
        #         self.assertEqual(case["expected"], case["instance"].is_leaf, msg=case)

        self.assertTrue(trees.SINGLETON.is_leaf)
        self.assertTrue(trees.NONEXISTENTPATH.is_leaf)
        self.assertFalse(trees.BINARY_TREE.is_leaf)
        self.assertTrue(trees.BINARY_TREE_SUBTREE.is_leaf)
        self.assertTrue(trees.COUNTDOWN.is_leaf)
        self.assertFalse(trees.SEQTREE.is_leaf)
        self.assertFalse(trees.INFINITE_TREE.is_leaf)

    def test_children(self):
        self.assertEqual(0, len(trees.SINGLETON.children))
        self.assertEqual(0, len(trees.NONEXISTENTPATH.children))
        self.assertEqual(2, len(trees.BINARY_TREE.children))
        self.assertEqual(0, len(trees.BINARY_TREE_SUBTREE.children))
        self.assertEqual(2, len(trees.INFINITE_BINARY_TREE.children))
        self.assertEqual(2, len(trees.INFINITE_BINARY_TREE_SUBTREE.children))
        self.assertEqual(0, len(trees.COUNTDOWN.children))
        self.assertEqual(1, len(trees.COUNTDOWN.root.children))
        self.assertEqual(3, len(trees.SEQTREE.children))
        self.assertEqual(1, len(trees.INFINITE_TREE.children))

    def test_leaves(self):
        self.assertEqual(1, trees.SINGLETON.leaves.count())
        self.assertEqual(1, trees.NONEXISTENTPATH.leaves.count())
        self.assertEqual(2, trees.BINARY_TREE.leaves.count())
        self.assertEqual(1, trees.BINARY_TREE_SUBTREE.leaves.count())
        self.assertEqual(1, trees.COUNTDOWN.leaves.count())
        self.assertEqual(1, trees.COUNTDOWN.root.leaves.count())
        self.assertEqual(4, trees.SEQTREE.leaves.count())

    def test_nodes(self):
        self.assertEqual(1, trees.SINGLETON.nodes.count())
        self.assertEqual(1, trees.NONEXISTENTPATH.nodes.count())
        self.assertEqual(5, trees.BINARY_TREE.nodes.count())
        self.assertEqual(1, trees.BINARY_TREE_SUBTREE.nodes.count())
        self.assertEqual(1, trees.COUNTDOWN.nodes.count())
        self.assertEqual(6, trees.COUNTDOWN.root.nodes.count())
        self.assertEqual(6, trees.SEQTREE.nodes.count())

    def test_descendants(self):
        self.assertEqual(0, trees.SINGLETON.descendants.count())
        self.assertEqual(0, trees.NONEXISTENTPATH.descendants.count())
        self.assertEqual(4, trees.BINARY_TREE.descendants.count())
        self.assertEqual(0, trees.BINARY_TREE_SUBTREE.descendants.count())
        self.assertEqual(0, trees.COUNTDOWN.descendants.count())
        self.assertEqual(5, trees.COUNTDOWN.root.descendants.count())
        self.assertEqual(5, trees.SEQTREE.descendants.count())

    def test_levels(self):
        self.assertEqual(1, trees.SINGLETON.levels.count())
        self.assertEqual(1, trees.NONEXISTENTPATH.levels.count())
        self.assertEqual(4, trees.BINARY_TREE.levels.count())
        self.assertEqual(1, trees.BINARY_TREE_SUBTREE.levels.count())
        self.assertEqual(1, trees.COUNTDOWN.levels.count())
        self.assertEqual(6, trees.COUNTDOWN.root.levels.count())
        self.assertEqual(3, trees.SEQTREE.levels.count())

    def test_preorder_nodes(self):
        tree = trees.BINARY_TREE
        values = [node.value for node, _ in tree.nodes.preorder()]
        expected = [1, 2, 3, 4, 5]
        self.assertEqual(expected, values)

    def test_preorder_descendants(self):
        tree = trees.BINARY_TREE
        values = [node.value for node, _ in tree.descendants.preorder()]
        expected = [2, 3, 4, 5]
        self.assertEqual(expected, values)

    def test_postorder_nodes(self):
        tree = trees.BINARY_TREE
        values = [node.value for node, _ in tree.nodes.postorder()]
        expected = [2, 5, 4, 3, 1]
        self.assertEqual(expected, values)

    def test_postorder_descendants(self):
        tree = trees.BINARY_TREE
        values = [node.value for node, _ in tree.descendants.postorder()]
        expected = [2, 5, 4, 3]
        self.assertEqual(expected, values)

    def test_levelorder_nodes(self):
        tree = trees.BINARY_TREE
        values = [node.value for node, _ in tree.nodes.levelorder()]
        expected = [1, 2, 3, 4, 5]
        self.assertEqual(expected, values)

    def test_levelorder_descendants(self):
        tree = trees.BINARY_TREE
        values = [node.value for node, _ in tree.descendants.levelorder()]
        expected = [2, 3, 4, 5]
        self.assertEqual(expected, values)
