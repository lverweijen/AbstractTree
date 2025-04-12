from abc import ABCMeta, abstractmethod
from collections import deque
from typing import Optional, Sequence

from .tree import DownTree, Tree, TNode, NodeItem
from .tree import NodesView


class BinaryDownTree(DownTree, metaclass=ABCMeta):
    """Binary-tree with links to children."""

    __slots__ = ()

    @property
    @abstractmethod
    def left_child(self) -> Optional[TNode]:
        raise None

    @property
    @abstractmethod
    def right_child(self) -> Optional[TNode]:
        raise None

    @property
    def children(self) -> Sequence[TNode]:
        nodes = list()
        if self.left_child is not None:
            nodes.append(self.left_child)
        if self.right_child is not None:
            nodes.append(self.right_child)
        return nodes

    @property
    def nodes(self):
        return BinaryNodesView([self], 0)

    @property
    def descendants(self):
        return BinaryNodesView(self.children, 1)


class BinaryTree(BinaryDownTree, Tree, metaclass=ABCMeta):
    """Binary-tree with links to children and to parent."""

    __slots__ = ()


class BinaryNodesView(NodesView):
    """Extend NodesView to make it do inorder."""

    __slots__ = ()

    def inorder(self, keep=None):
        """
        Iterate through nodes in inorder (traverse left, yield root, traverse right).

        Note:
        - `item.index` will be 0 for every left child
        - `item.index` will be 1 for every right child (even if node.left_child is None)
        This is a bit different from how `preorder()`, `postorder()` and `levelorder()` work,
        because those functions always give index 0 to the first child,
        regardless of whether it's a left or right child.
        Like the other iterators, the root of a subtree always gets item.index equal to 0,
        even if it is actually a right child in a bigger tree.
        """
        stack = deque()

        for index, node in enumerate(self.nodes):
            depth = self.level
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
