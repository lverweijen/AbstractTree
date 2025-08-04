import itertools
from abc import ABCMeta
from collections.abc import Iterator
from typing import Iterable, TypeVar

from .. import iterators as _iterators
from ..route import EdgesView, Route

T = TypeVar("T", bound="Tree")


class TreeView(Iterable[T], metaclass=ABCMeta):
    __slots__ = "_node"
    itr_method = None  # TODO Should __init_subclass__ be used instead?

    def __init__(self, node: T):
        self._node: T = node

    def __iter__(self) -> Iterator[T]:
        return type(self).itr_method(self._node)

    def __bool__(self) -> bool:
        try:
            next(iter(self))
        except StopIteration:
            return False
        else:
            return True

    def count(self) -> int:
        """Count number of nodes in this view."""
        return _ilen(self)


class AncestorsView(TreeView):
    """View over ancestors."""
    __slots__ = ()
    itr_method = _iterators.ancestors


class PathView(TreeView):
    """View over path from root to self."""
    __slots__ = ()
    itr_method = _iterators.path

    def __bool__(self):
        # A path always contains at least one node. No need to check.
        return True

    def __contains__(self, item):
        return item in reversed(self)

    def __reversed__(self):
        return _iterators.path(self._node, reverse=True)

    def to(self, other: T):
        return Route(self, other)

    def count(self):
        return _ilen(reversed(self))

    @property
    def edges(self):
        return EdgesView(self)


class NodesView(TreeView):
    """View over nodes."""
    __slots__ = "_include_root"
    itr_method = _iterators.nodes

    def __init__(self, node, include_root: bool = True):
        super().__init__(node)
        self._include_root = include_root

    def __iter__(self):
        return _iterators.nodes(self._node, include_root=self._include_root)

    def preorder(self, keep=None):
        return _iterators.preorder(self._node, keep, include_root=self._include_root)

    def postorder(self, keep=None):
        return _iterators.postorder(self._node, keep, include_root=self._include_root)

    def levelorder(self, keep=None):
        return _iterators.levelorder(self._node, keep, include_root=self._include_root)


class LeavesView(TreeView):
    """View over leaves."""
    __slots__ = ()
    itr_method = _iterators.leaves


class LevelsView(TreeView):
    """View over levels."""
    __slots__ = ()
    itr_method = _iterators.levels

    def __bool__(self):
        return True

    def zigzag(self):
        """Zig-zag through levels."""
        return _iterators.levels_zigzag(self._node)


class SiblingsView(TreeView):
    """View over siblings."""
    __slots__ = ()
    itr_method = _iterators.siblings

    def __contains__(self, other):
        try:
            other_parent = other.parent
        except AttributeError:
            return False  # not a Tree
        else:
            return other_parent is self._node.parent and other is not self._node

    def __len__(self):
        if p := self._node.parent:
            return len(p.children) - 1
        return 0

    count = __len__


class BinaryNodesView(NodesView):
    __slots__ = ()
    def inorder(self, keep=None):
        """
        Iterate through nodes in inorder (traverse left, yield root, traverse right).

        Note:
        - `item.index` will be 0 for every left child
        - `item.index` will be 1 for every right child (even if node.left_child is None)
        - `item.index` will be None for the root (even if root is a subtree)
        This is a bit different from how `preorder()`, `postorder()` and `levelorder()` work,
        because those functions always give index 0 to the first child,
        regardless of whether it's a left or right child.
        """
        if self._include_root:
            yield from _iterators._inorder(self._node, keep, index=None, depth=0)
        else:
            yield from _iterators._inorder(self._node.left_child, keep, index=0, depth=1)
            yield from _iterators._inorder(self._node.right_child, keep, index=1, depth=1)


def _ilen(itr):
    """Recipe from https://more-itertools.readthedocs.io/en/stable/api.html#more_itertools.ilen"""
    return sum(itertools.compress(itertools.repeat(1), zip(itr)))
