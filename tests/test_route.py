import unittest

from abstracttree.route import Route
from tests.tree_instances import INFINITE_BINARY_TREE, INFINITE_TREE, SEQTREE


class TestRoute(unittest.TestCase):
    def setUp(self):
        tree = INFINITE_BINARY_TREE
        r = tree.children[1]
        ll = tree.children[0].children[0]
        lll = ll.children[0]
        llr = ll.children[1]
        llrr = llr.children[1]

        self.tree = tree
        self.route1 = Route(tree, llrr, tree)
        self.route2 = Route(llrr, r, llrr, r)
        self.route3 = Route(r, r, tree, tree)
        self.route4 = Route(lll, llrr, llr)

    def test_anchors(self):
        result = [node.node for node in self.route1.anchors]
        self.assertEqual([0, 18, 0], result)
        self.assertEqual(3, len(self.route1.anchors))

        result = [node.node for node in self.route2.anchors]
        self.assertEqual([18, 2, 18, 2], result)
        self.assertEqual(4, len(self.route2.anchors))

        result = [node.node for node in self.route3.anchors]
        self.assertEqual([2, 2, 0, 0], result)
        self.assertEqual(4, len(self.route3.anchors))

        result = [node.node for node in self.route4.anchors]
        self.assertEqual([7, 18, 8], result)
        self.assertEqual(3, len(self.route4.anchors))

    def test_nodes(self):
        result = [node.node for node in self.route1.nodes]
        self.assertEqual([0, 1, 3, 8, 18, 8, 3, 1, 0], result)
        self.assertEqual(9, len(self.route1.nodes))

        result = [node.node for node in self.route2.nodes]
        self.assertEqual([18, 8, 3, 1, 0, 2, 0, 1, 3, 8, 18, 8, 3, 1, 0, 2], result)
        self.assertEqual(16, len(self.route2.nodes))

        result = [node.node for node in self.route3.nodes]
        self.assertEqual([2, 0], result)
        self.assertEqual(2, len(self.route3.nodes))

        result = [node.node for node in self.route4.nodes]
        self.assertEqual([7, 3, 8, 18, 8], result)
        self.assertEqual(5, len(self.route4.nodes))

    def test_edges(self):
        result = [(v1.node, v2.node) for (v1, v2) in self.route1.edges]
        expected = [(0, 1), (1, 3), (3, 8), (8, 18), (18, 8), (8, 3), (3, 1), (1, 0)]
        self.assertEqual(expected, result)
        self.assertEqual(8, len(self.route1.edges))

    def test_lca(self):
        self.assertEqual(0, self.route1.lca.node)
        self.assertEqual(0, self.route2.lca.node)
        self.assertEqual(0, self.route3.lca.node)
        self.assertEqual(3, self.route4.lca.node)

    def test_add_anchor(self):
        # Same tree
        self.route1.add_anchor(self.tree.root.children[0].root)

        # Different tree
        with self.assertRaises(ValueError):
            self.route1.add_anchor(SEQTREE)


if __name__ == '__main__':
    unittest.main()
