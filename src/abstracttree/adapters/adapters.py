from collections.abc import Sequence, Callable, Iterable
from functools import lru_cache
from typing import Optional, TypeVar, Type

import abstracttree.generics as generics
from abstracttree.generics import TreeLike, DownTreeLike
from abstracttree.mixins import Tree
from abstracttree.utils import eqv

T = TypeVar("T")


def convert_tree(tree: DownTreeLike, required_type=Type[T]) -> T:
    """Convert a TreeLike to a powerful Tree.

    If needed, it uses a TreeAdapter.
    """
    if isinstance(tree, required_type):
        return tree
    elif hasattr(tree, '_abstracttree_'):
        tree = tree._abstracttree_()
    else:
        tree = as_tree(tree)

    if isinstance(tree, required_type):
        return tree
    else:
        raise TypeError(f"Unable to convert {type(tree)} to {required_type}")


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
    cls = type(obj)
    adapter = compile_adapter(cls, children, parent, label)
    tree = adapter(obj)
    return tree


@lru_cache(maxsize=None)
def compile_adapter(
    cls,
    children: Callable[[T], Iterable[T]] = None,
    parent: Callable[[T], Optional[T]] = None,
    label: Callable[[T], str] = None,
):
    if not parent and issubclass(cls, TreeLike):
        parent = generics.parent.dispatch(cls)

    class CustomTreeAdapter(TreeAdapter):
        child_func = staticmethod(children or generics.children.dispatch(cls))
        parent_func = staticmethod(parent)
        label_func = staticmethod(label or generics.label.dispatch(cls))

    return CustomTreeAdapter

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

    def __str__(self) -> str:
        return self.label_func(self._value)

    @property
    def nid(self) -> int:
        return generics.nid(self._value)

    def __eq__(self, other) -> bool:
        """Check if the same node is wrapped. Similar to eqv(self.value, other.value)."""
        return eqv(self, other)

    def __hash__(self) -> int:
        """An adapter is hashable iff the underlying object is hashable."""
        return hash(self._value)

    @property
    def value(self):
        return self._value

    @property
    def parent(self: T) -> Optional[T]:
        if self._parent is not None:
            return self._parent

        cls = type(self)
        if pf := cls.parent_func:
            par = pf(self._value)
            if par is not None:
                return cls(par)
        return None

    @property
    def children(self: T) -> Sequence[T]:
        cls = type(self)
        _child_func = cls.child_func
        child_nodes = _child_func(self._value)
        return [cls(c, self) for c in child_nodes]
