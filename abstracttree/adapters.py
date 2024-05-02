import ast
import functools
import operator
import pathlib
import xml.etree.ElementTree as ET
import zipfile
from collections.abc import Sequence, Mapping
from typing import TypeVar, Callable, Iterable, overload, Collection, Union

from .tree import Tree, DownTree

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
    return UpgradedTree(tree)


@convert_tree.register
def _(tree: pathlib.PurePath):
    return PathTree(tree)


@convert_tree.register
def _(zf: zipfile.ZipFile):
    return PathTree(zipfile.Path(zf))


@convert_tree.register
def _(path: zipfile.Path):
    return PathTree(path)


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
def _(tree: Mapping):
    return MappingTree((None, tree))


@convert_tree.register
def _(cls: type, invert=False):
    if invert:
        return InvertedTypeTree(cls)
    return TypeTree(cls)


@convert_tree.register
def _(node: ast.AST):
    return AstTree(node)


@convert_tree.register
def _(element: ET.Element):
    return XmlTree(element)


@convert_tree.register
def _(tree: ET.ElementTree):
    return XmlTree(tree.getroot())


class TreeAdapter(Tree):
    __slots__ = "node"
    child_func: Callable[[TWrap], Iterable[TWrap]] = operator.attrgetter("children")
    parent_func: Callable[[TWrap], TWrap] = operator.attrgetter("parent")

    def __init__(self, node):
        self.node = node

    def __repr__(self):
        return f"{type(self).__name__}({self.node})"

    def __str__(self):
        return str(self.node)

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.node == other.node

    @property
    def nid(self):
        return id(self.node)

    def eqv(self, other):
        return isinstance(other, type(self)) and self.node is other.node

    @property
    def children(self):
        cls = self.__class__
        child_func = self.child_func
        return [cls(c) for c in child_func(self.node)]

    @property
    def parent(self):
        parent = self.parent_func(self.node)
        if parent is not None:
            return self.__class__(parent)
        else:
            return None


class PathTree(TreeAdapter):
    __slots__ = ()
    _custom_nids = {}

    @property
    def nid(self):
        try:  # Doesn't work on zipfile
            st = self.node.lstat()
        except (FileNotFoundError, AttributeError):
            return self._custom_nids.setdefault(str(self.node), len(self._custom_nids))
        else:
            return -st.st_ino

    def eqv(self, other):
        return self.node == other.node

    @staticmethod
    def parent_func(path):
        # pathlib makes parent an infinite, but we want None
        parent = path.parent
        if path != parent:
            return parent
        else:
            return None

    @property
    def children(self):
        try:
            return list(map(type(self), self.child_func(self.node)))
        except PermissionError:
            return []

    @staticmethod
    def child_func(p):
        return p.iterdir() if p.is_dir() else ()

    @property
    def root(self):
        return type(self)(type(self.node)(self.node.anchor))


class StoredParent(Tree):
    __slots__ = "node", "_parent"
    child_func: Callable[[TWrap], Iterable[TWrap]] = operator.attrgetter("children")

    def __init__(self, node, parent=None):
        self.node = node
        self._parent = parent

    def __repr__(self):
        return f"{type(self).__name__}({self.node})"

    def __str__(self):
        return str(self.node)

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.node == other.node

    @property
    def nid(self):
        return id(self.node)

    def eqv(self, other):
        return isinstance(other, type(self)) and self.node is other.node

    @property
    def children(self):
        cls = type(self)
        child_func = self.child_func
        return [cls(c, self) for c in child_func(self.node)]

    @property
    def parent(self):
        return self._parent


class UpgradedTree(StoredParent):
    __slots__ = ()

    @property
    def nid(self):
        return self.node.nid

    def eqv(self, other):
        return isinstance(other, type(self)) and self.node.eqv(other.node)


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
            return str(self.node)
        else:
            cls_name = type(self.node).__name__
            return f"{cls_name}[{len(self.node)}]"


class MappingTree(StoredParent):
    __slots__ = ()

    @staticmethod
    def child_func(item):
        _, value = item
        if isinstance(value, Mapping):
            return value.items()
        elif value is not None:
            return [(value, None)]
        else:
            return []

    @property
    def key(self):
        key, _ = self.node
        return key

    @property
    def mapping(self):
        _, mapping = self.node
        return mapping

    def __str__(self):
        key, mapping = self.node
        if self.is_root:
            cls_name = type(mapping).__name__
            return f"{cls_name}[{len(mapping)}]"
        else:
            return str(key)


class TypeTree(StoredParent):
    __slots__ = ()

    @property
    def nid(self):
        return id(self.node)

    @staticmethod
    def child_func(cls):
        return cls.__subclasses__()

    @property
    def parents(self):
        return list(map(type(self), self.node.__bases__))

    def __str__(self):
        return self.node.__qualname__


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
            return ast.dump(self.node)
        else:
            format_value = self.format_value
            args = [f"{name}={format_value(field)}" for name, field in ast.iter_fields(self.node)]
            joined_args = ", ".join(args)
            return f"{type(self.node).__name__}({joined_args})"

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


class XmlTree(StoredParent):
    @staticmethod
    def child_func(element):
        return element

    def __str__(self):
        element = self.node
        output = [f"<{element.tag}"]

        for k, v in element.items():
            output.append(f" {k}={v!r}")
        output.append(">")

        if text := element.text and str(element.text).strip():
            output.append(text)
            output.append(f"</{element.tag}>")
        if tail := element.tail and str(element.tail).strip():
            output.append(tail)

        return "".join(output)
