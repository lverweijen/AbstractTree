import operator
from abc import abstractmethod, ABCMeta
from typing import TypeVar, Callable, Optional, Collection, Literal, Iterable, Sequence

from .views import AncestorsView, PathView, NodesView, LeavesView, LevelsView, SiblingsView, BinaryNodesView
from .. import generics

TNode = TypeVar("TNode")
TMutDownNode = TypeVar("TMutDownNode", bound="MutableDownTree")
Order = Literal["pre", "post", "level"]


class AbstractTree(metaclass=ABCMeta):
    """Most abstract baseclass for everything."""

    __slots__ = ()

    @classmethod
    def convert(cls, obj):
        """Convert obj to tree-type or raise TypeError if that doesn't work."""
        # TODO Keep?
        from ..adapters import convert_tree
        return convert_tree(obj, cls)

    @property
    def nid(self) -> int:
        """Unique number that represents this node."""
        return id(self)


class UpTree(AbstractTree, metaclass=ABCMeta):
    """Abstract class for tree classes with parent but no children."""

    __slots__ = ()

    @property
    @abstractmethod
    def parent(self: TNode) -> Optional[TNode]:
        """Parent of this node or None if root."""
        return None

    @property
    def is_root(self) -> bool:
        """Whether this node is a root (has no parent)."""
        return self.parent is None

    @property
    def root(self) -> TNode:
        """Root of tree."""
        p, p2 = self, self.parent
        while p2:
            p, p2 = p2, p2.parent
        return p

    @property
    def ancestors(self):
        """View of ancestors of node."""
        return AncestorsView(self)

    @property
    def path(self):
        """View of path from root to node."""
        return PathView(self)


class DownTree(AbstractTree, metaclass=ABCMeta):
    """Abstract class for tree classes with children but no parent."""

    __slots__ = ()

    @property
    @abstractmethod
    def children(self: TNode) -> Collection[TNode]:
        """Children of this node."""
        return ()

    @property
    def leaves(self):
        """View of leaves from this node."""
        return LeavesView(self)

    @property
    def nodes(self):
        """View of this node and its descendants."""
        return NodesView(self)

    @property
    def descendants(self):
        """View of descendants of this node."""
        return NodesView(self, include_root=False)

    @property
    def levels(self):
        """View of this node and descendants by level."""
        return LevelsView(self)

    @property
    def is_leaf(self) -> bool:
        """Whether this node is a leaf (does not have children)."""
        return not self.children

    def transform(self: TNode, f: Callable[[TNode], TMutDownNode], keep=None) -> TMutDownNode:
        """Create new tree where each node of self is transformed by f."""
        stack = []
        for node, item in self.descendants.postorder(keep=keep):
            depth = item.depth
            while len(stack) < depth:
                stack.append(list())
            stack[depth - 1].append(new := f(node))
            if len(stack) > depth:
                new.add_children(stack.pop(-1))
        new = f(self)
        if stack:
            new.add_children(stack.pop())
        return new


class MutableDownTree(DownTree, metaclass=ABCMeta):
    """Abstract class for mutable tree with children."""

    __slots__ = ()

    @abstractmethod
    def add_child(self, node: TNode):
        """Add node to children."""
        raise NotImplementedError

    @abstractmethod
    def remove_child(self, node: TNode):
        """Remove node from children."""
        raise NotImplementedError

    def add_children(self, children: Iterable[TNode]):
        """Add multiple nodes to children."""
        for child in children:
            self.add_child(child)


class Tree(UpTree, DownTree, metaclass=ABCMeta):
    """Abstract class for tree classes with access to children and parents."""

    __slots__ = ()

    @property
    def siblings(self):
        """View of siblings of this node."""
        return SiblingsView(self)


class MutableTree(Tree, MutableDownTree, metaclass=ABCMeta):
    """Abstract class for mutable tree with children and parent."""

    __slots__ = ()

    def detach(self) -> TNode:
        """Remove parent if any and return self."""
        if p := self.parent:
            p.remove_child(self)
        return self


class BinaryDownTree(DownTree, metaclass=ABCMeta):
    """Binary-tree with links to children."""

    __slots__ = ()

    @property
    @abstractmethod
    def left_child(self) -> Optional[TNode]:
        return None

    @property
    @abstractmethod
    def right_child(self) -> Optional[TNode]:
        return None

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
        return BinaryNodesView(self)

    @property
    def descendants(self):
        return BinaryNodesView(self, include_root=False)


class BinaryTree(BinaryDownTree, Tree, metaclass=ABCMeta):
    """Binary-tree with links to children and to parent."""

    __slots__ = ()


# Some optimizations
generics.children.register(DownTree, operator.attrgetter("children"))
generics.parent.register(UpTree, operator.attrgetter("parent"))
generics.nid.register(AbstractTree, operator.attrgetter("nid"))
generics.label.register(AbstractTree, str)
