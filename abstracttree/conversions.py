import ast
import functools
import operator
import pathlib
import zipfile
from collections.abc import Sequence
from typing import TypeVar, Callable, Iterable, overload, Collection, Union

from .treeclasses import Tree, DownTree

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
            class CustomTree(TreeAdapter):
                child_func = staticmethod(children)
                parent_func = staticmethod(parent)
        else:
            class CustomTree(StoredParent):
                child_func = staticmethod(children)
        return CustomTree(obj)


@functools.singledispatch
def convert_tree(tree):
    """Low level conversion of tree object to an abstracttree.Tree.

    The default implementation ducktypes on `tree.parent` and `tree.children`.
    """
    if hasattr(tree, "children"):
        if hasattr(tree, "parent"):
            return TreeAdapter(tree)
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
    return PathTree(tree)


@convert_tree.register
def _(file: zipfile.ZipFile):
    return PathTree(zipfile.Path(file))


@convert_tree.register
def _(tree: Sequence):
    return SequenceTree(tree)


@convert_tree.register(str)
@convert_tree.register(bytes)
@convert_tree.register(bytearray)
def _(_: BaseString):
    raise NotImplementedError("astree(x: str | bytes | bytearray) is unsafe, "
                              "because x is infinitely recursively iterable.")


@convert_tree.register
def _(cls: type, invert=False):
    if invert:
        return InvertedTypeTree(cls)
    return TypeTree(cls)


@convert_tree.register
def _(node: ast.AST):
    return AstTree(node)


class TreeAdapter(Tree):
    __slots__ = "value"
    child_func: Callable[[TWrap], Iterable[TWrap]] = operator.attrgetter("children")
    parent_func: Callable[[TWrap], TWrap] = operator.attrgetter("parent")

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f"{type(self).__name__}({self.value})"

    def __str__(self):
        return str(self.value)

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.value == other.value

    @property
    def nid(self):
        return id(self.value)

    def eqv(self, other):
        return isinstance(other, type(self)) and self.value is other.value

    @property
    def children(self):
        cls = self.__class__
        child_func = self.child_func
        return [cls(c) for c in child_func(self.value)]

    @property
    def parent(self):
        parent = self.parent_func(self.value)
        if parent is not None:
            return self.__class__(parent)
        else:
            return None


class PathTree(TreeAdapter):
    __slots__ = ()

    def nid(self):
        try:
            # Not implemented on zipfile.Path
            st = self.value.lstat()
        except (FileNotFoundError, AttributeError):
            return -id(self.value)
        else:
            return st.st_ino

    def eqv(self, other):
        return self.value == other.value

    @staticmethod
    def parent_func(path):
        # pathlib makes parent an infinite, but we want None
        parent = path.parent
        if path != parent:
            return parent
        else:
            return None

    @staticmethod
    def child_func(p):
        try:
            return p.iterdir() if p.is_dir() else ()
        except PermissionError:
            # Ignore
            return ()

    @property
    def root(self):
        return type(self)(type(self.value)(self.value.anchor))


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
        return isinstance(other, type(self)) and self.value == other.value

    @property
    def nid(self):
        return id(self.value)

    def eqv(self, other):
        return isinstance(other, type(self)) and self.value is other.value

    @property
    def children(self):
        cls = type(self)
        child_func = self.child_func
        return [cls(c, self) for c in child_func(self.value)]

    @property
    def parent(self):
        return self._parent


class SequenceTree(StoredParent):
    __slots__ = ()

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


class TypeTree(StoredParent):
    __slots__ = ()

    @staticmethod
    def child_func(cls):
        return cls.__subclasses__()

    def __str__(self):
        return self.value.__qualname__


class InvertedTypeTree(TypeTree):
    __slots__ = ()

    @staticmethod
    def child_func(cls):
        return cls.__bases__


class AstTree(StoredParent):
    __slots__ = ()
    CONT = '↓'
    SINGLETON = Union[ast.expr_context, ast.boolop, ast.operator, ast.unaryop, ast.cmpop]

    @classmethod
    def child_func(cls, node):
        return tuple(node for node in ast.iter_child_nodes(node) if cls.is_child(node))

    @classmethod
    def is_child(cls, node):
        return isinstance(node, ast.AST) and not isinstance(node, cls.SINGLETON)

    def __str__(self):
        if self.is_leaf:
            return ast.dump(self.value)
        else:
            format_value = self.format_value
            args = [f"{name}={format_value(field)}" for name, field in ast.iter_fields(self.value)]
            joined_args = ", ".join(args)
            return f"{type(self.value).__name__}({joined_args})"

    @classmethod
    def format_value(cls, field):
        if cls.is_child(field):
            field_str = cls.CONT
        elif isinstance(field, ast.AST):
            field_str = ast.dump(field)
        elif isinstance(field, Sequence) and not isinstance(field, BaseString):
            field = [cls.format_value(f) for f in field]
            field_str = "[" + ", ".join(field) + "]"
        else:
            field_str = repr(field)
        return field_str
