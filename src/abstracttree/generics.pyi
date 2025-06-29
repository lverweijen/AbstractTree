"""
Provide static typing for generics.py

Unfortunately, static type checkers can't handle __subclasshook__.
Therefore, type stubs are provided for TreeLike and DownTreeLike.
"""

import ast
import zipfile
from collections.abc import Collection, Sequence
from functools import singledispatch
from pathlib import Path
from typing import Self, TypeVar, Optional, Any, Protocol, overload, Never


class _HasChildren(Protocol):
    @property
    def children(self) -> Collection[Self]:
        ...


class _HasChildrenAndParent(_HasChildren):
    @property
    def parent(self) -> Self:
        ...

TreeLike = _HasChildrenAndParent | Path | zipfile.Path | type
DownTreeLike = TreeLike | _HasChildren | Collection | ast.AST

try:
    DownTreeLike |= ExceptionGroup
except AttributeError:
    pass

T = TypeVar("T", bound=TreeLike)
DT = TypeVar("DT", bound=DownTreeLike)


@singledispatch
@overload
def children(tree: str | bytes | bytearray) -> Never: ...
@overload
def children(tree: Collection) -> Any: ...
@overload
def children(tree: DT) -> Collection[DT]: ...

@singledispatch
def parent(tree: T) -> Optional[T]: ...

@singledispatch
def parents(tree: T) -> Sequence[T]: ...

@singledispatch
def root(node: T) -> T: ...

@singledispatch
def label(node: object) -> str: ...

@singledispatch
def nid(node: Any): ...
