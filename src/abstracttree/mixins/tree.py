from abc import abstractmethod, ABCMeta
from collections import namedtuple
from typing import TypeVar, Callable, Optional, Collection, Literal, Iterable

from ._views import AncestorsView, PathView, NodesView, LeavesView, LevelsView, SiblingsView

TNode = TypeVar("TNode")
TMutDownNode = TypeVar("TMutDownNode", bound="MutableDownTree")
Order = Literal["pre", "post", "level"]
NodeItem = namedtuple("NodeItem", ["index", "depth"])
NodePredicate = Callable[[TNode, NodeItem], bool]


class AbstractTree(metaclass=ABCMeta):
    """Most abstract baseclass for everything."""

    __slots__ = ()

    @classmethod
    def convert(cls, obj):
        """Convert obj to tree-type or raise TypeError if that doesn't work."""
        from ..adapters import convert_tree

        if isinstance(obj, cls):
            return obj
        tree = convert_tree(obj)
        if isinstance(tree, cls):
            return tree
        raise TypeError(f"{obj!r} cannot be converted to {cls.__name__}")

    @property
    def nid(self) -> int:
        """Unique number that represents this node."""
        return id(self)

    def eqv(self, other) -> bool:
        """Check if both objects represent the same node.

        Should normally be operator.is, but can be overridden by delegates.
        """
        return self is other


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
