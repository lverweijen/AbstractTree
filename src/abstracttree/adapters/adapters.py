from collections.abc import Sequence, Mapping, Collection, Callable, Iterable
from typing import Optional, TypeVar

import abstracttree.generics as generics
from abstracttree.generics import TreeLike
from abstracttree.mixins.tree import Tree, TNode

T = TypeVar("T")


def convert_tree(tree: TreeLike) -> Tree:
    """Convert a TreeLike to a powerful Tree.

    If needed, it uses a TreeAdapter.
    """
    if isinstance(tree, Tree):
        return tree
    elif isinstance(tree, Sequence | Mapping):
        return CollectionTreeAdapter(tree)
    else:
        return TreeAdapter(tree)


def as_tree(
    obj: T,
    children: Callable[[T], Iterable[T]] = None,
    parent: Callable[[T], Optional[T]] = None,
    label: Callable[[T], str] = None,
) -> "TreeAdapter":
    """Convert any object to a tree.

    Functions can be passed to control how the conversion should be done.
    The original object can be accessed by using the value attribute.
    """
    children = children or generics.children
    parent = parent or generics.parent
    label = label or generics.label

    class CustomTreeAdapter(TreeAdapter):
        child_func = staticmethod(children)
        parent_func = staticmethod(parent)
        label_func = staticmethod(label)

    return CustomTreeAdapter(obj)

# Alias for backwards compatibility
astree = as_tree


class TreeAdapter(Tree):
    child_func = staticmethod(generics.children)
    parent_func = staticmethod(generics.parent)
    label_func = staticmethod(generics.label)

    def __init__(self, value: TreeLike, _parent=None):
        self._value = value
        self._parent = _parent

    def __repr__(self) -> str:
        return f"{type(self).__qualname__}({self.value!r})"

    def __str__(self):
        return self.label_func(self._value)

    def nid(self) -> int:
        return id(self._value)

    def eqv(self, other) -> bool:
        return self.value is other.value

    def __eq__(self, other):
        return self.value == other.value

    @property
    def value(self):
        return self._value

    @property
    def parent(self: TNode) -> Optional[TNode]:
        if self._parent is not None:
            return self._parent
        cls = type(self)
        try:
            parent = cls.parent_func(self._value)
        except TypeError:
            return None
        else:
            if parent is not None:
                return cls(parent)
            else:
                return None

    @property
    def children(self: TNode) -> Sequence[TNode]:
        cls = type(self)
        _child_func = cls.child_func
        try:
            child_nodes = _child_func(self._value)
        except TypeError:
            return ()
        else:
            return [cls(c, self) for c in child_nodes]


class CollectionTreeAdapter(TreeAdapter):
    """Same as TreeView, but a non-collection is always a leaf.

    This is convenient if the collection contains tree-like objects (e.g. Path) that should not be handled recursively.
    """

    @property
    def children(self: TNode) -> Sequence[TNode]:
        value = self._value
        if not isinstance(value, Collection) or isinstance(value, generics.BaseString):
            return ()
        else:
            return super().children
