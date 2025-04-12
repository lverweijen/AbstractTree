from pathlib import Path
from unittest import TestCase

import tree_instances as trees
from abstracttree import as_tree


class TestUpTree(TestCase):
    def test_parent(self):
        path_parent = as_tree(Path("this/path/should/not"))
        self.assertEqual(None, trees.SINGLETON.parent)
        self.assertEqual(str(path_parent), str(trees.NONEXISTENTPATH.parent))  # Or should there be an eqv generic that does samefile?
        self.assertEqual(None, trees.INFINITE_BINARY_TREE.parent)
        self.assertEqual(2, trees.INFINITE_BINARY_TREE_SUBTREE.parent.value)
        self.assertEqual(4, trees.COUNTDOWN.parent.value)
        self.assertEqual(trees.INFINITE_TREE, trees.INFINITE_TREE)

    def test_root(self):
        path_root = as_tree(Path(""))
        self.assertEqual(trees.SINGLETON, trees.SINGLETON.root)
        self.assertEqual(str(path_root), str(trees.NONEXISTENTPATH.root))
        self.assertEqual(0, trees.INFINITE_BINARY_TREE.root.value)
        self.assertEqual(0, trees.INFINITE_BINARY_TREE_SUBTREE.root.value)
        self.assertEqual(0, trees.COUNTDOWN.root.value)

    def test_is_root(self):
        self.assertTrue(trees.SINGLETON.is_root)
        self.assertFalse(trees.NONEXISTENTPATH.is_root)
        self.assertTrue(trees.INFINITE_BINARY_TREE.is_root)
        self.assertFalse(trees.INFINITE_BINARY_TREE_SUBTREE.is_root)
        self.assertFalse(trees.COUNTDOWN.is_root)
        self.assertFalse(trees.INFINITE_TREE.is_root)

    def test_ancestors(self):
        self.assertEqual(0, trees.SINGLETON.ancestors.count())
        self.assertEqual(5, trees.NONEXISTENTPATH.ancestors.count())
        self.assertEqual(0, trees.INFINITE_BINARY_TREE.ancestors.count())
        self.assertEqual(2, trees.INFINITE_BINARY_TREE_SUBTREE.ancestors.count())
        self.assertEqual(5, trees.COUNTDOWN.ancestors.count())

    def test_path(self):
        self.assertEqual(1, trees.SINGLETON.path.count())
        self.assertEqual(6, trees.NONEXISTENTPATH.path.count())
        self.assertEqual(1, trees.INFINITE_BINARY_TREE.path.count())
        self.assertEqual(3, trees.INFINITE_BINARY_TREE_SUBTREE.path.count())
        self.assertEqual(6, trees.COUNTDOWN.path.count())
