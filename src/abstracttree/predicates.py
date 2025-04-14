from dataclasses import dataclass
from typing import Callable, TypeVar

from ._iterators import NodeItem
from .generics import TreeLike, DownTreeLike, nid, parent

T = TypeVar("T", bound=TreeLike)
DT = TypeVar("DT", bound=DownTreeLike)


class Predicate(Callable[[T, NodeItem], bool]):
    __slots__ = ()

    def __or__(self, other):
        if other is None:
            return None
        else:
            return PredicateUnion(self, other)

    def __and__(self, other):
        if other is None:
            return self
        else:
            return PredicateIntersection(self, other)


class PredicateUnion(Predicate):
    __slots__ = "preds"

    def __init__(self, *preds):
        self.preds = preds

    def __call__(self, node: DT, item: NodeItem):
        return any(pred(node, item) for pred in self.preds)


class PredicateIntersection(Predicate):
    __slots__ = "preds"

    def __init__(self, *preds):
        self.preds = preds

    def __call__(self, node: DT, item: NodeItem):
        return all(pred(node, item) for pred in self.preds)


class RemoveDuplicates(Predicate):
    """Remove duplicates in case of cycles or multiparent trees."""

    __slots__ = "seen"

    def __init__(self):
        self.seen = set()

    def __call__(self, node: DT, item):
        node_nid = nid(node)
        if node_nid in self.seen:
            return False
        else:
            self.seen.add(node_nid)
            return True


class PreventCycles(Predicate):
    """Prevent looping cyclic trees.

    It might yield nodes more than once, but will not repeat children.
    This is mostly useful when trying to plot cyclic trees.
    """

    __slots__ = "seen", "duplicates"

    def __init__(self):
        self.seen = set()
        self.duplicates = set()

    def __call__(self, node: DT, item):
        p = parent(node)
        node_nid = nid(node)

        if p is not None and nid(p) in self.duplicates and node_nid in self.seen:
            return False
        if node_nid in self.seen:
            self.duplicates.add(node_nid)
        else:
            self.seen.add(node_nid)
        return True


# From python 3.10, add slots=True
@dataclass(frozen=True)
class MaxDepth(Predicate):
    """Limit iteration to a certain depth

    Can be passed to keep argument of methods such as tree.iter_tree().
    >>> from littletree import Node
    >>> tree = Node(identifier='root').path.create(['a', 'b', 'c', 'd']).root
    >>> [node.identifier for node in tree.nodes.preorder(keep=MaxDepth(3))]
    ['root', 'a', 'b', 'c']
    """

    depth: int

    def __call__(self, _node, item):
        return item.depth <= self.depth
