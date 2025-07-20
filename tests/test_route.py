import unittest

from abstracttree.route import Route
from tests.tree_instances import INFINITE_BINARY_TREE, SEQTREE, HEAP_TREE


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

        self.heap_route = Route(HEAP_TREE.children[0], HEAP_TREE.children[1])

    def test_anchors(self):
        result = [node.value for node in self.route1.anchors]
        self.assertEqual([0, 18, 0], result)
        self.assertEqual(3, len(self.route1.anchors))

        result = [node.value for node in self.route2.anchors]
        self.assertEqual([18, 2, 18, 2], result)
        self.assertEqual(4, len(self.route2.anchors))

        result = [node.value for node in self.route3.anchors]
        self.assertEqual([2, 2, 0, 0], result)
        self.assertEqual(4, len(self.route3.anchors))

        result = [node.value for node in self.route4.anchors]
        self.assertEqual([7, 18, 8], result)
        self.assertEqual(3, len(self.route4.anchors))

        result = [node.index for node in self.heap_route.anchors]
        self.assertEqual([1, 2], result)
        self.assertEqual(3, len(self.route4.anchors))

    def test_nodes(self):
        result = [node.value for node in self.route1.nodes]
        self.assertEqual([0, 1, 3, 8, 18, 8, 3, 1, 0], result)
        self.assertEqual(9, len(self.route1.nodes))

        result = [node.value for node in self.route2.nodes]
        self.assertEqual([18, 8, 3, 1, 0, 2, 0, 1, 3, 8, 18, 8, 3, 1, 0, 2], result)
        self.assertEqual(16, len(self.route2.nodes))

        result = [node.value for node in self.route3.nodes]
        self.assertEqual([2, 0], result)
        self.assertEqual(2, len(self.route3.nodes))

        result = [node.value for node in self.route4.nodes]
        self.assertEqual([7, 3, 8, 18, 8], result)
        self.assertEqual(5, len(self.route4.nodes))

        result = [node.value for node in self.heap_route.nodes]
        self.assertEqual([1, 0, 3], result)
        self.assertEqual(3, len(self.heap_route.nodes))

    def test_edges(self):
        result = [(v1.value, v2.value) for (v1, v2) in self.route1.edges]
        expected = [(0, 1), (1, 3), (3, 8), (8, 18), (18, 8), (8, 3), (3, 1), (1, 0)]
        self.assertEqual(expected, result)
        self.assertEqual(8, len(self.route1.edges))

    def test_reversed(self):
        node_result = [node.value for node in reversed(self.route2.nodes)]
        edge_result = [(v1.value, v2.value) for (v1, v2) in reversed(self.route2.edges)]
        node_expected = [2, 0, 1, 3, 8, 18, 8, 3, 1, 0, 2, 0, 1, 3, 8, 18]
        edge_expected = [
            (2, 0),
            (0, 1),
            (1, 3),
            (3, 8),
            (8, 18),
            (18, 8),
            (8, 3),
            (3, 1),
            (1, 0),
            (0, 2),
            (2, 0),
            (0, 1),
            (1, 3),
            (3, 8),
            (8, 18),
        ]
        self.assertEqual(node_expected, node_result)
        self.assertEqual(edge_expected, edge_result)

    def test_lca(self):
        self.assertEqual(0, self.route1.lca.value)
        self.assertEqual(0, self.route2.lca.value)
        self.assertEqual(0, self.route3.lca.value)
        self.assertEqual(3, self.route4.lca.value)
        self.assertEqual(0, self.heap_route.lca.index)

    def test_add_anchor(self):
        # Same tree
        self.route1.add_anchor(self.tree.root.children[0].root)

        # Different tree
        with self.assertRaises(ValueError):
            self.route1.add_anchor(SEQTREE)

    def test_paths(self):
        from pathlib import Path
        p1 = Path(__file__)
        p2 = Path(__file__).parent.parent / "src"

        res = [node.name for node in Route(p1, p2).nodes]
        self.assertEqual(['test_route.py', 'tests', 'abstracttree', 'src'], res)


if __name__ == "__main__":
    unittest.main()
