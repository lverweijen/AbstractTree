import itertools
from abc import ABCMeta
from collections import deque
from typing import Iterable, TypeVar

from .. import _iterators
from ..generics import TreeLike

T = TypeVar("T", bound=TreeLike)


class TreeView(Iterable[T], metaclass=ABCMeta):
    __slots__ = "_node"
    itr_method = None

    def __init__(self, node):
        self._node = node

    def __iter__(self):
        return type(self).itr_method(self._node)

    def __bool__(self):
        try:
            next(iter(self))
        except StopIteration:
            return False
        else:
            return True

    def count(self) -> int:
        """Count number of nodes in this view."""
        counter = itertools.count()
        deque(zip(self, counter), maxlen=0)
        return next(counter)


class AncestorsView(TreeView):
    """View over ancestors."""
    itr_method = _iterators.ancestors


class PathView(TreeView):
    """View over path from root to self."""
    itr_method = _iterators.path

    def __bool__(self):
        # A path always contains at least one node. No need to check.
        return True

    def __contains__(self, item):
        return item in reversed(self)

    def __reversed__(self):
        return _iterators.path(self._node, reverse=True)

    def count(self):
        counter = itertools.count()
        deque(zip(reversed(self), counter), maxlen=0)
        return next(counter)


class NodesView(TreeView):
    """View over nodes."""
    __slots__ = "_include_root"

    def __init__(self, node, include_root: bool = True):
        super().__init__(node)
        self._include_root = include_root

    def __iter__(self):
        nodes = deque([self._node] if self._include_root else self._node.children)
        while nodes:
            yield (node := nodes.pop())
            nodes.extend(node.children)

    def preorder(self, keep=None):
        return _iterators.preorder(self._node, keep, include_root=self._include_root)

    def postorder(self, keep=None):
        return _iterators.postorder(self._node, keep, include_root=self._include_root)

    def levelorder(self, keep=None):
        return _iterators.levelorder(self._node, keep, include_root=self._include_root)


class LeavesView(TreeView):
    """View over leaves."""
    itr_method = _iterators.leaves


class LevelsView(TreeView):
    """View over levels."""
    itr_method = _iterators.levels

    def __bool__(self):
        return True

    def zigzag(self):
        """Zig-zag through levels."""
        return _iterators.levels_zigzag(self._node)


class SiblingsView(TreeView):
    """View over siblings."""
    itr_method = _iterators.siblings

    def __contains__(self, node):
        return not self._node is node and node.parent is self._node.parent

    def __len__(self):
        if p := self._node.parent:
            return len(p.children) - 1
        return 0

    count = __len__
