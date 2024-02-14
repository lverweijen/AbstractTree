"""
In networkx a tree is called an arborescence.

We can build a Tree-interface around such an arborescence.
Since networkx has a very different data model it makes most sense to work with delegates.
"""

import networkx as nx

from abstracttree import print_tree
from abstracttree.conversions import TreeAdapter


class NetworkXTree(TreeAdapter):
    @property
    def nid(self):
        return id(self.identifier)

    @property
    def graph(self):
        (graph, _) = self.node
        return graph

    @property
    def identifier(self):
        (graph, identifier) = self.node
        return identifier

    @property
    def data(self):
        (graph, label) = self.node
        return graph.nodes[label]

    def __str__(self):
        return f"{self.identifier}"

    @staticmethod
    def child_func(node):
        (graph, label) = node
        for child in graph.successors(label):
            yield graph, child

    @staticmethod
    def parent_func(node):
        (graph, label) = node
        parents = list(graph.predecessors(label))
        if len(parents) > 1:
            raise nx.NotATree("Node has multiple parents.")
        elif not parents:
            return None
        else:
            return graph, parents[0]


def graph_to_tree(graph: nx.Graph, node=None, check=True):
    if check and not nx.is_arborescence(graph):
        raise nx.NotATree("An arborescence is expected.")

    if not node:
        for node in graph.nodes:
            break
        else:
            raise ValueError("graph needs at least one node")

    return NetworkXTree((graph, node)).root


def main():
    import networkx as nx
    graph = nx.DiGraph()
    graph.add_node(1)
    graph.add_edge(1, 2)
    graph.add_edge(1, 3)
    graph.add_edge(0, 1)

    tree = graph_to_tree(graph)
    print_tree(tree)

    # graph can still be edited using networkx and changes will be reflected on tree

main()
