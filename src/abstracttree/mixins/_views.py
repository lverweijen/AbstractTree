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

    def __bool__(self):
        return self._node.parent is not None


class PathView(TreeView):
    """View over path from root to self."""
    itr_method = _iterators.ancestors

    def __iter__(self):
        seq = list(type(self).itr_method(self._node))
        return itertools.chain(reversed(seq), [self._node])

    def __reversed__(self):
        seq = type(self).itr_method(self._node)
        return itertools.chain([self._node], seq)


class NodesView(TreeView):
    """View over nodes."""
    __slots__ = "include_root"

    def __init__(self, node, include_root: bool = True):
        super().__init__(node)
        self.include_root = include_root

    def __iter__(self):
        nodes = deque([self._node] if self.include_root else self._node.children)
        while nodes:
            yield (node := nodes.pop())
            nodes.extend(node.children)

    def preorder(self, keep=None):
        return _iterators.preorder(self._node, keep, include_root=self.include_root)

    def postorder(self, keep=None):
        return _iterators.postorder(self._node, keep, include_root=self.include_root)

    def levelorder(self, keep=None):
        return _iterators.levelorder(self._node, keep, include_root=self.include_root)


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
