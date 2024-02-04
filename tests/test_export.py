from unittest import TestCase

from abstracttree import to_string, to_mermaid, to_dot, MaxDepth
from tree_instances import INFINITE_TREE, BINARY_TREE


class TestExport(TestCase):
    def test_to_string(self):
        result = to_string(INFINITE_TREE, keep=MaxDepth(2))
        expected = 3 * 'Infinite singleton!\n'
        self.assertEqual(expected, result)

        result = to_string(BINARY_TREE)
        expected = [
            '(1)',
            '├─ (2)',
            '└─ (3)',
            '   └─ (4)',
            '      └─ (5)',
        ]
        self.assertEqual(expected, result.splitlines())

    def test_to_dot(self):
        result = to_dot(INFINITE_TREE, node_name=str)
        expected = ('strict digraph tree {\n'
                    '"Infinite singleton!"[label="Infinite singleton!"];\n'
                    '"Infinite singleton!"[label="Infinite singleton!"];\n'
                    '"Infinite singleton!"->"Infinite singleton!";\n'
                    '}\n')
        self.assertEqual(expected, result)

        result = to_dot(BINARY_TREE, node_name=str)
        expected = ('strict digraph tree {\n'
                    '"(1)"[label="(1)"];\n'
                    '"(2)"[label="(2)"];\n'
                    '"(3)"[label="(3)"];\n'
                    '"(4)"[label="(4)"];\n'
                    '"(5)"[label="(5)"];\n'
                    '"(1)"->"(2)";\n'
                    '"(1)"->"(3)";\n'
                    '"(3)"->"(4)";\n'
                    '"(4)"->"(5)";\n'
                    '}\n')
        self.assertEqual(expected, result)

    def test_to_mermaid(self):
        result = to_mermaid(INFINITE_TREE, node_name=lambda n: str(n)[:3])
        expected = ('graph TD;\n'
                    'Inf[Infinite singleton!];\n'
                    'Inf[Infinite singleton!];\n'
                    'Inf-->Inf;\n')
        self.assertEqual(expected, result)

        result = to_mermaid(BINARY_TREE, node_name=lambda n: str(n)[1:-1])
        expected = ('graph TD;\n'
                    '1[(1)];\n'
                    '2[(2)];\n'
                    '3[(3)];\n'
                    '4[(4)];\n'
                    '5[(5)];\n'
                    '1-->2;\n'
                    '1-->3;\n'
                    '3-->4;\n'
                    '4-->5;\n')
        self.assertEqual(expected, result)
