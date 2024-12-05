import shutil
from unittest import TestCase

from abstracttree import to_string, to_mermaid, to_dot, MaxDepth, to_latex, to_image
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

    def test_to_image(self):
        if not shutil.which("dot"):
            self.skipTest("Program dot not found")
        tree_bytes = to_image(BINARY_TREE, file_format='svg')
        tree_xml = tree_bytes.decode('utf-8')
        self.assertTrue(tree_xml.startswith("<?xml"))

    def test_to_latex(self):
        result = to_latex(BINARY_TREE, node_label=lambda n: str(n)[1:-1])
        expected = (
            '\\begin{tikzpicture}[align=center,\n'
            'level 1/.style = {sibling distance = 1*2em},\n'
            'level 2/.style = {sibling distance = 1*2em},\n'
            'level 3/.style = {sibling distance = 1*2em}]\n'
            '\\node{1} [grow=right]\n'
            '    child {node {2}}\n'
            '    child {node {3}\n'
            '        child {node {4}\n'
            '            child {node {5}}\n'
            '        }\n'
            '    }\n'
            '\\end{tikzpicture}')
        self.assertEqual(expected, result)

        result = to_latex(["root",
                           [["james", "steve"],
                            ["patrick", "mike", "bodé", "pete", "mama", "mia"],
                            "ortega"]])
        expected = (
            '\\begin{tikzpicture}[align=center,\n'
            'level 1/.style = {sibling distance = 6*2em},\n'
            'level 2/.style = {sibling distance = 4*2em},\n'
            'level 3/.style = {sibling distance = 1*2em}]\n'
            '\\node{list[2]} [grow=right]\n'
            '    child {node {root}}\n'
            '    child {node {list[3]}\n'
            '        child {node {list[2]}\n'
            '            child {node {james}}\n'
            '            child {node {steve}}\n'
            '        }\n'
            '        child {node {list[6]}\n'
            '            child {node {patrick}}\n'
            '            child {node {mike}}\n'
            '            child {node {bodé}}\n'
            '            child {node {pete}}\n'
            '            child {node {mama}}\n'
            '            child {node {mia}}\n'
            '        }\n'
            '        child {node {ortega}}\n'
            '    }\n'
            '\\end{tikzpicture}')
        self.assertEqual(expected, result)

        difficult_tree = [
            [['a', 'b', 'c', 'd', 'e', 'f', ['g']]],
            [1],
            [2],
            [[[3]]],
            [[4, 5, 6, 7, 8, 9, 10]],
        ]
        result = to_latex(difficult_tree)
        expected = (
            '\\begin{tikzpicture}[align=center,\n'
            'level 1/.style = {sibling distance = 4*2em},\n'
            'level 2/.style = {sibling distance = 4*2em},\n'
            'level 3/.style = {sibling distance = 1*2em},\n'
            'level 4/.style = {sibling distance = 1*2em}]\n'
            '\\node{list[5]} [grow=right]\n'
            '    child {node {list[1]}\n'
            '        child {node {list[7]}\n'
            '            child {node {a}}\n'
            '            child {node {b}}\n'
            '            child {node {c}}\n'
            '            child {node {d}}\n'
            '            child {node {e}}\n'
            '            child {node {f}}\n'
            '            child {node {list[1]}\n'
            '                child {node {g}}\n'
            '            }\n'
            '        }\n'
            '    }\n'
            '    child {node {list[1]}\n'
            '        child {node {1}}\n'
            '    }\n'
            '    child {node {list[1]}\n'
            '        child {node {2}}\n'
            '    }\n'
            '    child {node {list[1]}\n'
            '        child {node {list[1]}\n'
            '            child {node {list[1]}\n'
            '                child {node {3}}\n'
            '            }\n'
            '        }\n'
            '    }\n'
            '    child {node {list[1]}\n'
            '        child {node {list[7]}\n'
            '            child {node {4}}\n'
            '            child {node {5}}\n'
            '            child {node {6}}\n'
            '            child {node {7}}\n'
            '            child {node {8}}\n'
            '            child {node {9}}\n'
            '            child {node {10}}\n'
            '        }\n'
            '    }\n'
            '\\end{tikzpicture}')
        self.assertEqual(expected, result)
