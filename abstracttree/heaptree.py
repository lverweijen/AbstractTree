from typing import Collection, Optional

from .treeclasses import Tree, TNode


class HeapTree(Tree):
    """Provides a tree interface to a heap.

    Mainly useful for visualisation purposes.
    >>> from abstracttree import print_tree
    >>> import heapq
    >>> tree = HeapTree()
    >>> for n in range(5, 0, -1):
    >>>     heapq.heappush(tree.heap, n)
    >>> print_tree(tree)
    1
    ├─ 2
    │  ├─ 5
    │  └─ 4
    └─ 3
    """
    __slots__ = "heap", "index"

    def __init__(self, heap=None, index=0):
        if heap is None:
            heap = []
        self.heap = heap
        self.index = index

    def __str__(self):
        try:
            return repr(self.value)
        except IndexError:
            return repr(self)

    @property
    def nid(self):
        return self.index

    def eqv(self, other):
        return type(self) is type(other) and self.index == other.index

    @property
    def children(self: TNode) -> Collection[TNode]:
        return [HeapTree(self.heap, i)
                for i in range(2 * self.index + 1, 2 * self.index + 3)
                if i < len(self.heap)]

    @property
    def parent(self: TNode) -> Optional[TNode]:
        return HeapTree(self.heap, (self.index - 1) // 2)

    @property
    def value(self):
        return self.heap[self.index]
