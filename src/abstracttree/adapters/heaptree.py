from collections.abc import MutableSequence
from typing import Collection, Optional, TypeVar

from ..mixins import BinaryTree

D = TypeVar("D")


class HeapTree(BinaryTree):
    """Provides a tree interface to a heap.

    Mainly useful for visualisation purposes.
    >>> from abstracttree import print_tree
    >>> import heapq
    >>> tree = HeapTree()
    >>> for n in range(5, 0, -1):
    >>>     heapq.heappush(tree.heap, n)
    >>> print_tree(tree)
    0 → 1
    ├─ 1 → 2
    │  ├─ 3 → 5
    │  └─ 4 → 4
    └─ 2 → 3
    """

    __slots__ = "_heap", "_index"

    def __init__(self, heap: MutableSequence[D] = None, index: int = 0):
        if heap is None:
            heap = []
        self._heap = heap
        self._index = index

    def __repr__(self):
        return f"{type(self).__qualname__}{self._heap, self._index}"

    def __str__(self):
        try:
            return f"{self._index} → {self.value}"
        except IndexError:
            return repr(self)

    @property
    def nid(self):
        return (id(self._heap) << 32) | self._index

    @property
    def heap(self) -> MutableSequence[D]:
        return self._heap

    @property
    def index(self):
        return self._index

    @property
    def value(self) -> D:
        return self._heap[self._index]

    def __eq__(self, other):
        """Nodes should refer to the same _heap (identity) with the same _index."""
        return (isinstance(other, HeapTree)
                and self._heap is other._heap
                and self._index == other._index)

    def __hash__(self):
        """Hashes by id(list) and _index."""
        return hash((id(self._heap), self._index))

    @property
    def children(self) -> Collection["HeapTree"]:
        return [
            HeapTree(self._heap, i)
            for i in range(2 * self._index + 1, 2 * self._index + 3)
            if i < len(self._heap)
        ]

    @property
    def left_child(self) -> Optional["HeapTree"]:
        i = 2 * self._index + 1
        if i < len(self._heap):
            return HeapTree(self._heap, i)

    @property
    def right_child(self) -> Optional["HeapTree"]:
        i = 2 * self._index + 2
        if i < len(self._heap):
            return HeapTree(self._heap, i)

    @property
    def parent(self) -> Optional["HeapTree"]:
        n = self._index
        if n != 0:
            return HeapTree(self._heap, (n - 1) // 2)
        else:
            return None
