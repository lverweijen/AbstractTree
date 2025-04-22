import itertools
from collections import namedtuple, deque
from collections.abc import Iterator, Sequence
from typing import TypeVar

import abstracttree.generics as generics

NodeItem = namedtuple("NodeItem", ["index", "depth"])

T = TypeVar("T", bound=generics.TreeLike)
DT = TypeVar("DT", bound=generics.DownTreeLike)


def ancestors(node: T) -> Iterator[T]:
    """Iterate through ancestors of node."""
    parent = generics.parent.dispatch(type(node))
    while (node := parent(node)) is not None:
        yield node


def path(node: T, reverse=False) -> Iterator[T]:
    """Iterate through path of node."""
    if not reverse:
        return itertools.chain(reversed(list(ancestors(node))), [node])
    else:
        return itertools.chain([node], reversed(list(ancestors(node))))


def preorder(tree: DT, keep=None, include_root=True) -> Iterator[tuple[DT, NodeItem]]:
    """Iterate through nodes in pre-order.

    Only descend where keep(node).
    Returns tuples (node, item)
    Item denotes depth of iteration and index of child.
    """
    children = generics.children.dispatch(type(tree))
    if include_root:
        nodes = deque([(tree, NodeItem(None, 0))])
    else:
        nodes = deque(reversed([(c, NodeItem(i, 1)) for i, c in enumerate(children(tree))]))

    while nodes:
        node, item = nodes.pop()
        if not keep or keep(node, item):
            yield node, item
            next_nodes = [(c, NodeItem(i, item.depth + 1)) for i, c in enumerate(children(node))]
            nodes.extend(reversed(next_nodes))


def postorder(tree: DT, keep=None, include_root=True) -> Iterator[tuple[DT, NodeItem]]:
    """Iterate through nodes in post-order.

    Only descend where keep(node).
    Returns tuples (node, item)
    Item denotes depth of iteration and index of child.
    """
    children = generics.children.dispatch(type(tree))

    if include_root:
        nodes = iter([(tree, NodeItem(None, 0))])
    else:
        nodes = iter([(c, NodeItem(i, 1)) for i, c in enumerate(children(tree))])

    node, item = next(nodes, (None, None))
    stack = []

    while node or stack:
        # Go down
        keep_node = keep is None or keep(node, item)
        while keep_node and (cc := children(node)):
            stack.append((node, item, nodes))
            nodes = iter([
                (c, NodeItem(i, item.depth + 1)) for (i, c) in enumerate(cc)
            ])
            node, item = next(nodes)
            keep_node = keep is None or keep(node, item)
        if keep_node:
            yield node, item

        # Go right or go up
        node, item = next(nodes, (None, None))
        while node is None and stack:
            node, item, nodes = stack.pop()
            yield node, item
            node, item = next(nodes, (None, None))


def levelorder(tree: DT, keep=None, include_root=True) -> Iterator[tuple[DT, NodeItem]]:
    """Iterate through nodes in level-order.

    Only descend where keep(node).
    Returns tuples (node, item)
    Item denotes depth of iteration and index of child.
    """
    children = generics.children.dispatch(type(tree))
    if include_root:
        nodes = deque([(tree, NodeItem(None, 0))])
    else:
        nodes = deque([(c, NodeItem(i, 1)) for i, c in enumerate(children(tree))])

    while nodes:
        node, item = nodes.popleft()
        if not keep or keep(node, item):
            yield node, item
            next_nodes = [(c, NodeItem(i, item.depth + 1)) for i, c in enumerate(children(node))]
            nodes.extend(next_nodes)


def leaves(tree: DT) -> Iterator[DT]:
    """Iterate through leaves of node."""
    children = generics.children.dispatch(type(tree))
    for node, _ in preorder(tree):
        if not children(node):
            yield node


def siblings(node: T) -> Iterator[T]:
    """Iterate through siblings of node."""
    nid = generics.nid.dispatch(type(node))
    node_nid = nid(node)
    if p := generics.parent(node):
        return (child for child in generics.children(p) if node_nid != nid(child))
    else:
        return iter(())


def levels(tree: DT) -> Iterator[Sequence[DT]]:
    """Iterate through descendants in levels."""
    children = generics.children.dispatch(type(tree))
    level = [tree]
    while level:
        yield iter(level)
        level = [child for node in level for child in children(node)]


def levels_zigzag(tree: DT) -> Iterator[Sequence[DT]]:
    """Iterate through descendants in levels in zigzag-order."""
    children = generics.children.dispatch(type(tree))
    level = [tree]
    while level:
        yield iter(level)
        level = [child for node in reversed(level) for child in reversed(children(node))]


def _inorder(node, keep=None, index=None, depth=0):
    """Iterate through nodes of BinaryTree.

    This requires node to be a BinaryTree.
    It's less generic than the other methods. Therefore, it's not exported by default.
    It can be accessed through mixins.views.BinaryNodes.
    """
    stack = deque()
    item = NodeItem(index, depth)

    while node is not None or stack:
        # Traverse down/left
        left_child, left_item = node.left_child, NodeItem(0, depth + 1)
        while left_child is not None and (not keep or keep(left_child, left_item)):
            stack.append((node, item))
            node, item, depth = left_child, left_item, depth + 1
            left_child, left_item = node.left_child, NodeItem(0, depth + 1)

        yield node, item

        # Traverse right/up
        right_child, right_item = node.right_child, NodeItem(1, depth + 1)
        while stack and (
                right_child is None or (keep and not keep(right_child, right_item))
        ):
            node, item = stack.pop()
            yield node, item
            depth -= 1
            right_child, right_item = node.right_child, NodeItem(1, depth + 1)
        node, item, depth = right_child, right_item, depth + 1
