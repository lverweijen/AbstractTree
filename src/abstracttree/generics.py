import ast
import itertools
import operator
import os
import xml.etree.ElementTree as ET
import zipfile
from abc import ABCMeta
from collections import namedtuple
from collections.abc import Sequence, Mapping, Collection
from functools import singledispatch
from pathlib import Path
from typing import TypeVar, Optional, Union

BaseString = Union[str, bytes, bytearray]
BasePath = Union[Path, zipfile.Path]
MappingItem = namedtuple("MappingItem", ["key", "value"])



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


DT = TypeVar("DT", bound=TreeLike)
T = TypeVar("T", bound=DownTreeLike)


# Base cases
@singledispatch
def children(tree: DT) -> Sequence[DT]:
    """Returns children of any downtreelike-object."""
    try:
        return tree.children
    except AttributeError:
        raise TypeError(f"{type(tree)} is not DownTreeLike. Children not defined.") from None

@singledispatch
def parent(tree: T) -> Optional[T]:
    """Returns parent of any treelike-object."""
    try:
        return tree.parent
    except AttributeError:
        raise TypeError(f"{type(tree)} is not TreeLike. Parent not defined.") from None

@singledispatch
def parents(multitree: T) -> Sequence[T]:
    """Like parent(tree) but return value as a sequence."""
    tree_parent = parent(multitree)
    if tree_parent is not None:
        return (tree_parent,)
    else:
        return ()

@singledispatch
def root(node: T):
    """Find the root of a node in a tree."""
    maybe_parent = parent(node)
    while maybe_parent is not None:
        node, maybe_parent = maybe_parent, parent(maybe_parent)
    return node

@singledispatch
def label(node: object) -> str:
    """Return a string representation of this node.

    This representation should always represent just the Node.
    If the node has parents or children these should be omitted.
    """
    ...
label.register(object, str)

@singledispatch
def nid(node: object):
    try:
        return node.nid()
    except AttributeError:
        return id(node)

@singledispatch
def eqv(node, node2):
    """Whether 2 nodes reference the same object."""
    try:
        return node.eqv(node2)
    except AttributeError:
        return node is node2


# Collections (Handle Mapping, Sequence and BaseString together to allow specialisation).
@children.register
def _(coll: Collection):
    match coll:
        case Mapping():
            return [MappingItem(k, v) for k, v in coll.items()]
        case MappingItem():  #value=value):
            value = coll.value
            if isinstance(value, Collection) and not isinstance(value, BaseString):
                return children(value)
            else:
                return [value]
        case Collection() if not isinstance(coll, BaseString):
            return coll
        case _:
            return ()

@label.register
def _(coll: Collection):
    """In python a type can have multiple parent classes."""
    match coll:
        case MappingItem(key=key):
            return str(key)
        case Collection() if not isinstance(coll, BaseString):
            cls_name = type(coll).__name__
            return f"{cls_name}[{len(coll)}]"
        case _:
            return str(coll)


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


# BasePath
@children.register
def _(pth: BasePath):
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
def _(pth: BasePath):
    parent_path = pth.parent
    if pth != parent_path:
        return parent_path
    else:
        return None

@label.register
def _(pth: BasePath):
    return pth.name

@root.register
def _(pth: BasePath):
    return pth.anchor


# PathLike (not fully supported, except for Path)
@nid.register
def _(pth: os.PathLike):
    # Some paths are circular. nid can be used to stop recursion in those cases.
    try:
        st = os.lstat(pth)
    except (FileNotFoundError, AttributeError):
        return id(pth)  # Fall-back
    else:
        return -st.st_ino

@eqv.register
def _(p1: os.PathLike, p2: os.PathLike) -> bool:
    return p1 == p2 or os.path.samefile(p1, p2)

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


# XML / ElementTree.Element
@children.register
def _(element: ET.Element):
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
