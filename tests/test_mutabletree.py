from unittest import TestCase

from abstracttree import MaxDepth

try:
    from .tree_instances import BinaryNode, INFINITE_BINARY_TREE
except ImportError:
    from tree_instances import BinaryNode, INFINITE_BINARY_TREE


class TestMutableDownTree(TestCase):
    def setUp(self):
        tree = BinaryNode(1)  # 2 children
        tree.left = BinaryNode(2)  # leaf
        tree.right = BinaryNode(3)  # 1 child left
        tree.right.left = BinaryNode(4)  # 1 child right
        tree.right.left.right = BinaryNode(5)  # leaf
        self.tree = tree

    def test_add_child(self):
        tree = self.tree
        tree.left.add_child(BinaryNode(-1))
        values = [node.value for node, _ in tree.nodes.preorder()]
        expected = [1, 2, -1, 3, 4, 5]
        self.assertEqual(expected, values)

    def test_remove_child(self):
        tree = self.tree
        tree.remove_child(self.tree.right)
        values = [node.value for node, _ in tree.nodes.preorder()]
        expected = [1, 2]
        self.assertEqual(expected, values)

    def test_transform(self):
        def double(node):
            return BinaryNode(2 * node.value)

        double_tree = self.tree.transform(double)
        values = [node.value for node, _ in double_tree.nodes.preorder()]
        expected = [2, 4, 6, 8, 10]
        self.assertEqual(expected, values)

    def test_transform_II(self):
        """Test keep attribute on infinite tree.

        This is a pretty cool way to convert an infinite tree to a finite one.
        """

        def double(node):
            return BinaryNode(value=2 * node.value)

        double_tree = INFINITE_BINARY_TREE.transform(double, keep=MaxDepth(2))
        values = [node.value for node, _ in double_tree.nodes.preorder()]
        expected = [0, 2, 6, 8, 4, 10, 12]
        self.assertEqual(expected, values)
