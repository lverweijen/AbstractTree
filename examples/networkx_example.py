"""
In networkx a tree is called an arborescence.

We can build a Tree-interface around such an arborescence.
Since networkx has a very different data model it makes most sense to work with delegates.
"""

import networkx as nx

from abstracttree import print_tree
from abstracttree.adapters import TreeAdapter


class NetworkXTree(TreeAdapter):
    @property
    def graph(self):
        (graph, _) = self.value
        return graph

    @property
    def identifier(self):
        (_, identifier) = self.value
        return identifier

    @property
    def data(self):
        (graph, identifier) = self.value
        return graph.nodes[identifier]

    def __str__(self):
        return f"{self.identifier}"

    @staticmethod
    def child_func(node):
        (graph, identifier) = node
        for child in graph.successors(identifier):
            yield graph, child

    @staticmethod
    def parent_func(node):
        (graph, identifier) = node
        parents = list(graph.predecessors(identifier))
        if len(parents) > 1:
            raise nx.NotATree("Node has multiple parents.")
        elif not parents:
            return None
        else:
            return graph, parents[0]

    @property
    def nid(self):
        return id(self.graph) << 32 | id(self.identifier)


def graph_to_tree(graph: nx.Graph, node=None, check=True):
    if check and not nx.is_arborescence(graph):
        raise nx.NotATree("An arborescence is expected.")

    resolve_root = node is None
    tree = NetworkXTree((graph, node or any(graph.nodes)))
    if resolve_root:
        tree = tree.root

    return tree


def main():
    graph = nx.DiGraph()
    graph.add_node(1)
    graph.add_edge(1, 2)
    graph.add_edge(1, 3)
    graph.add_edge(0, 1)

    tree = graph_to_tree(graph)
    print_tree(tree)

    # Find sibling of node 2
    node_2 = graph_to_tree(graph, node=2)
    for sibling in node_2.siblings:
        print("sibling of node 2 = {!r}".format(sibling.identifier))

    # graph can still be edited using networkx and changes will be reflected on tree


if __name__ == '__main__':
    main()
