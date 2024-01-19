import ast
import functools
import operator
import pathlib
from collections.abc import Sequence
from typing import TypeVar, Callable, Iterable, overload, Collection, Union

from treeclasses import Tree, DownTree

TWrap = TypeVar("TWrap")
BaseString = Union[str, bytes, bytearray]  # Why did they ever remove this type?


@overload
def astree(obj) -> Tree:
    ...


@overload
def astree(obj: TWrap, children: Callable[[TWrap], Collection[TWrap]]) -> Tree:
    ...


@overload
def astree(obj: TWrap,
           children: Callable[[TWrap], Collection[TWrap]],
           parent: Callable[[TWrap], TWrap]) -> Tree:
    ...


def astree(
    obj: TWrap,
    children: Callable[[TWrap], Iterable[TWrap]] = None,
    parent: Callable[[TWrap], TWrap] = None,
) -> Tree:
    """Convert an arbitrary object into a tree.

    If no children or parents are given it will try a standard conversion.
    If children and parents are given, they will be used as a function.
    If children, but no parent is given, it will create a tree that has obj as its root.
    """
    if not children:
        return convert_tree(obj)
    else:
        if parent:
            class CustomTree(TreeView):
                child_func = staticmethod(children)
                parent_func = staticmethod(parent)
        else:
            class CustomTree(StoredParent):
                child_func = staticmethod(children)
        return CustomTree(obj)


@functools.singledispatch
def convert_tree(tree):
    """Low level conversion of tree object to an abstracttree.Tree.

    The default implementation ducktypes on tree.parent and tree.children
    """
    if hasattr(tree, "children"):
        if hasattr(tree, "parent"):
            return TreeView(tree)
        else:
            return StoredParent(tree)
    else:
        raise NotImplementedError


@convert_tree.register
def _(tree: Tree):
    return tree


@convert_tree.register
def _(tree: DownTree):
    return StoredParent(tree)


@convert_tree.register
def _(tree: pathlib.PurePath):
    return PathTreeView(tree)


@convert_tree.register
def _(tree: Sequence):
    if isinstance(tree, BaseString):
        return NotImplemented
    return SequenceStoredParent(tree)


@convert_tree.register(str)
@convert_tree.register(bytes)
@convert_tree.register(bytearray)
def _(_: BaseString):
    raise NotImplementedError("astree(x: str | bytes | bytearray) is unsafe, "
                              "because it is an infinite sequence.")


@convert_tree.register
def _(cls: type, invert=False):
    if invert:
        return InvertedTypeStoredParent(cls)
    return TypeStoredParent(cls)


@convert_tree.register
def _(node: ast.AST):
    return AstStoredParent(node)


class TreeView(Tree):
    __slots__ = "value", "_parent"
    child_func: Callable[[TWrap], Iterable[TWrap]] = operator.attrgetter("children")
    parent_func: Callable[[TWrap], TWrap] = operator.attrgetter("parent")

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f"{type(self).__name__}({self.value})"

    def __str__(self):
        return str(self.value)

    def __eq__(self, other):
        return self.value == other.value

    @property
    def children(self):
        cls = self.__class__
        child_func = self.child_func
        return [cls(c) for c in child_func(self.value)]

    @property
    def parent(self):
        return self.__class__(self.parent_func)


class PathTreeView(TreeView):
    @staticmethod
    def child_func(p):
        return p.iterdir() if p.is_dir() else (),


class StoredParent(Tree):
    __slots__ = "value", "_parent"
    child_func: Callable[[TWrap], Iterable[TWrap]] = operator.attrgetter("children")

    def __init__(self, value, parent=None):
        self.value = value
        self._parent = parent

    def __repr__(self):
        return f"{type(self).__name__}({self.value})"

    def __str__(self):
        return str(self.value)

    def __eq__(self, other):
        return self.value == other.value

    @property
    def children(self):
        cls = type(self)
        child_func = self.child_func
        return [cls(c, self) for c in child_func(self.value)]

    @property
    def parent(self):
        return self._parent


class SequenceStoredParent(StoredParent):
    @staticmethod
    def child_func(seq):
        if isinstance(seq, Sequence) and not isinstance(seq, BaseString):
            return seq
        else:
            return ()

    def __str__(self):
        if self.is_leaf:
            return str(self.value)
        else:
            cls_name = type(self.value).__name__
            return f"{cls_name}[{len(self.value)}]"


class TypeStoredParent(StoredParent):
    @staticmethod
    def child_func(cls):
        return cls.__subclasses__()

    def __str__(self):
        return self.value.__qualname__


class InvertedTypeStoredParent(TypeStoredParent):
    @staticmethod
    def child_func(cls):
        return cls.__bases__


class AstStoredParent(StoredParent):
    CONT = '↓'

    @staticmethod
    def child_func(node):
        return tuple(ast.iter_child_nodes(node))

    def __str__(self):
        cont = self.CONT
        if self.is_leaf:
            return ast.dump(self.value)
        else:
            args = []
            for name, field in ast.iter_fields(self.value):
                if isinstance(field, Sequence):
                    field = [cont if isinstance(f, ast.AST) else repr(f) for f in field]
                    field_str = "[" + ", ".join(field) + "]"
                    args.append(f"{name}={field_str}")
                elif isinstance(field, ast.AST):
                    args.append(f"{name}={cont}")
                else:
                    args.append(f"{name}={field!r}")

            joined_args = ", ".join(args)
            return f"{type(self.value).__name__}({joined_args})"
