import heapq
from pathlib import Path

from abstracttree import BinaryDownTree, MutableDownTree, Tree, as_tree, HeapTree


class BinaryNode(MutableDownTree, BinaryDownTree):
    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None

    def __str__(self):
        return f"({self.value})"

    @property
    def left_child(self):
        return self.left

    @property
    def right_child(self):
        return self.right

    def add_child(self, node):
        if self.left is None:
            self.left = node
        elif self.right is None:
            self.right = node
        else:
            raise Exception("Binary node is full")

    def remove_child(self, node):
        if node is self.left:
            self.left = None
        elif node is self.right:
            self.right = None
        else:
            raise Exception("Not my child")


class InfiniteSingleton(Tree):
    @property
    def children(self):
        return [self]

    @property
    def parent(self):
        return self

    def __str__(self):
        return "Infinite singleton!"


SINGLETON = as_tree("Singleton", children=lambda n: ())
NONEXISTENTPATH = as_tree(Path("this/path/should/not/exist"))

BINARY_TREE = BinaryNode(1)  # 2 children
BINARY_TREE.left = BinaryNode(2)  # leaf
BINARY_TREE.right = BinaryNode(3)  # 1 child left
BINARY_TREE.right.left = BinaryNode(4)  # 1 child right
BINARY_TREE.right.left.right = BinaryNode(5)  # leaf

BINARY_TREE_SUBTREE = BINARY_TREE.right.left.right

INFINITE_BINARY_TREE = as_tree(0, children=lambda n: (2 * n + 1, 2 * n + 2))
INFINITE_BINARY_TREE_SUBTREE = INFINITE_BINARY_TREE.children[1].children[0]

COUNTDOWN_MAX = 5
COUNTDOWN = as_tree(
    COUNTDOWN_MAX,
    children=lambda n: [n + 1] if n < COUNTDOWN_MAX else (),
    parent=lambda n: n - 1 if n > 0 else None,
)

SEQTREE = as_tree([1, [2, 3], []])

INFINITE_TREE = InfiniteSingleton()

HEAP_TREE = HeapTree([5, 4, 3, 2, 1, 0])
heapq.heapify(HEAP_TREE.heap)
