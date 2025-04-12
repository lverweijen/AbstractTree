import ast
import itertools
import os
import xml.etree.ElementTree as ET
import zipfile
from abc import ABCMeta
from collections import namedtuple
from collections.abc import Sequence, Mapping, Iterable, Collection
from functools import singledispatch
from pathlib import Path
from typing import TypeVar, Optional, Union

T = TypeVar("T")


class DownTreeLike(metaclass=ABCMeta):
    """Any object that has an identifiable parent and/or identifiable children."""
    @classmethod
    def __subclasshook__(cls, subclass):
        has_children = (hasattr(subclass, "children")
                        or children.dispatch(object) is not children.dispatch(subclass))
        return has_children

    @property
    def children(self):
        return ()


class TreeLike(metaclass=ABCMeta):
    """Any object that has an identifiable parent."""
    @classmethod
    def __subclasshook__(cls, subclass):
        has_parent = (hasattr(subclass, "parent")
                      or parent.dispatch(object) is not parent.dispatch(subclass))
        return has_parent and issubclass(subclass, DownTreeLike)

    @property
    def parent(self):
        return None


# Base cases
@singledispatch
def children(tree: T) -> Sequence[T]:
    try:
        return tree.children
    except AttributeError:
        raise TypeError("This is not a DownTree.") from None

@singledispatch
def parent(tree: T) -> Optional[T]:
    try:
        return tree.parent
    except AttributeError:
        raise TypeError("That is not a tree.") from None

@singledispatch
def path(node: TreeLike):
    """Find path from root to node."""
    ancestors = [node]
    while (node := parent(node)) is not None:
        ancestors.append(node)
    return reversed(ancestors)

@singledispatch
def parents(multitree: T) -> Sequence[T]:
    """Like parent(tree) but return value is a sequence."""
    tree_parent = parent(multitree)
    if tree_parent is not None:
        return (tree_parent,)
    else:
        return ()

@singledispatch
def root(node):
    """Find the root of a node in a tree."""
    maybe_parent = parent(node)
    while maybe_parent is not None:
        node, maybe_parent = maybe_parent, parent(maybe_parent)
    return node

@singledispatch
def label(node) -> str:
    """Return a string representation of this node.

    This representation should always represent just the Node.
    If the node has parents or children these should be omitted.
    """
    try:
        return node.label()
    except AttributeError:
        return str(node)

@singledispatch
def eqv(node, node2):
    """Whether 2 nodes reference the same object."""
    try:
        return node.eqv(node2)
    except AttributeError:
        return node is node2


# Collections
@children.register
def _(coll: Collection):
    return coll

@label.register
def _(coll: Collection):
    """In python a type can have multiple parent classes."""
    cls_name = type(coll).__name__
    return f"{cls_name}[{len(coll)}]"


# Mappings
MappingItem = namedtuple("MappingItem", ["key", "value"])

@children.register
def _(mapping: Mapping):
    return [MappingItem(k, v) for k, v in mapping.items()]

@children.register
def _(item: MappingItem):
    value = item.value
    if isinstance(value, Collection) and not isinstance(value, BaseString):
        return children(value)
    else:
        return [value]

@label.register
def _(item: MappingItem):
    return str(item.key)


# BaseString
BaseString = Union[str, bytes, bytearray]

@children.register
def _(_: BaseString):
    # Prevent a string from becoming a tree with infinite depth
    raise TypeError("String-types aren't trees.")

@label.register
def _(text: BaseString):
    return str(text)


# Types
@children.register
def _(cls: type):
    return cls.__subclasses__()

@parents.register
def _(cls: type):
    """In python a type can have multiple parent classes. Therefore, parent is not defined."""
    return cls.__bases__

@label.register
def _(cls: type):
    return cls.__qualname__

@root.register
def _(_: type) -> type:
    return object


# PathLike
@children.register
def _(pth: os.PathLike | zipfile.ZipFile | zipfile.Path):
    if isinstance(pth, os.PathLike):
        pth = Path(pth)
    elif isinstance(pth, zipfile.ZipFile):
        pth = zipfile.Path(pth)

    if pth.is_dir():
        try:
            return tuple(pth.iterdir())
        except PermissionError:
            # Print error and continue
            import traceback
            traceback.print_exc()
            return ()
    else:
        return ()

@parent.register
def _(pth: os.PathLike | zipfile.Path):
    if isinstance(pth, os.PathLike):
        pth = Path(pth)
    parent_path = pth.parent
    if pth != parent_path:
        return parent_path
    else:
        return None

@root.register
def _(pth: os.PathLike) -> Path:
    return Path(Path(pth).anchor)

@eqv.register
def _(p1: os.PathLike, p2: os.PathLike) -> bool:
    return os.path.samefile(p1, p2)

@path.register
def _(pth: os.PathLike) -> Iterable[Path]:
    pth = Path(pth)
    return itertools.chain(reversed(pth.parents), [pth])

@label.register
def _(zf: Path | zipfile.Path):
    return zf.name

@label.register
def _(pth: os.PathLike):
    return os.path.basename(pth)


# AST
AST_SINGLETON = Union[ast.expr_context, ast.boolop, ast.operator, ast.unaryop, ast.cmpop]
AST_CONT = "↓"

@children.register
def _(node: ast.AST):
    return tuple(child for child in ast.iter_child_nodes(node)
                 if isinstance(child, ast.AST) and not isinstance(child, AST_SINGLETON))

@label.register
def _(node: ast.AST):
    def format_value(field):
        if isinstance(field, ast.AST):
            if isinstance(field, AST_SINGLETON):
                field_str = ast.dump(field)
            else:
                field_str = AST_CONT
        elif isinstance(field, Sequence) and not isinstance(field, BaseString):
            field = [format_value(f) for f in field]
            field_str = "[" + ", ".join(field) + "]"
        else:
            field_str = repr(field)
        return field_str

    node_children = children(node)

    if not node_children:
        return ast.dump(node)
    else:
        # format_value = format_value(node)
        args = [f"{name}={format_value(field)}" for name, field in ast.iter_fields(node)]
        joined_args = ", ".join(args)
        return f"{type(node).__name__}({joined_args})"


# XML / ElementTree
@children.register
def _(element: ET.Element | ET.ElementTree):
    if isinstance(element, ET.ElementTree):
        element = element.getroot()

    return element

@label.register
def _(element: ET.Element):
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
