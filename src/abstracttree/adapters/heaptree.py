from typing import Collection, Optional

from ..mixins import BinaryTree


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

    __slots__ = "heap", "index"

    def __init__(self, heap=None, index=0):
        if heap is None:
            heap = []
        self.heap = heap
        self.index = index

    def __repr__(self):
        return f"{type(self).__qualname__}{self.heap, self.index}"

    def __str__(self):
        try:
            return f"{self.index} → {self.value}"
        except IndexError:
            return repr(self)

    @property
    def nid(self):
        return (id(self.heap) << 32) | self.index

    def __eq__(self, other):
        """Nodes should refer to the same heap (identity) with the same index."""
        return self.heap is other.heap and self.index == other.index

    @property
    def children(self) -> Collection["HeapTree"]:
        return [
            HeapTree(self.heap, i)
            for i in range(2 * self.index + 1, 2 * self.index + 3)
            if i < len(self.heap)
        ]

    @property
    def left_child(self) -> Optional["HeapTree"]:
        i = 2 * self.index + 1
        if i < len(self.heap):
            return HeapTree(self.heap, i)

    @property
    def right_child(self) -> Optional["HeapTree"]:
        i = 2 * self.index + 2
        if i < len(self.heap):
            return HeapTree(self.heap, i)

    @property
    def parent(self) -> Optional["HeapTree"]:
        n = self.index
        if n != 0:
            return HeapTree(self.heap, (n - 1) // 2)
        else:
            return None

    @property
    def value(self):
        return self.heap[self.index]
