import itertools
from bisect import bisect
from collections.abc import Sequence, MutableSequence
from typing import TypeVar, Optional, Generic

from abstracttree import iterators as _iterators
from abstracttree.generics import TreeLike, nid

T = TypeVar("T", bound=TreeLike)


class Route(Generic[T]):
    """Representation of a route trough adjacent nodes in the tree.

    Two nodes are adjacent if they have a parent-child relationship.
    The route will be as short as possible, but it will visit the anchor points in order.
    """

    __slots__ = "_anchor_paths", "_ancestor_levels"

    def __init__(self, *anchors: T):
        """Create a route through a few nodes.

        All nodes should belong to the same tree.
        """
        self._anchor_paths: MutableSequence[Sequence[T]] = []
        self._ancestor_levels = []

        for anchor in anchors:
            self.add_anchor(anchor)

    def __repr__(self):
        nodes_str = ", ".join([repr(anchor) for anchor in self.anchors])
        return f"{self.__class__.__name__}({nodes_str})"

    def add_anchor(self, anchor: T):
        """Add a node to the route.

        The node should belong to the same tree as any existing anchor nodes.
        """

        anchor_path = list(_iterators.path(anchor))

        if self._anchor_paths:
            last_path = self._anchor_paths[-1]
            if anchor_path[0] != last_path[0]:
                raise ValueError("Different tree!")
            self._ancestor_levels.append(_common2(last_path, anchor_path))

        self._anchor_paths.append(anchor_path)

    def __iter__(self):
        if len(self._anchor_paths) < 2:
            yield from self.anchors
        path_j = None
        for (path_i, path_j), level in zip(itertools.pairwise(self._anchor_paths), self._ancestor_levels):
            yield from path_i[:level:-1]
            yield from path_j[level:-1]
        if path_j is not None:
            yield path_j[-1]

    def __reversed__(self):
        if len(self._anchor_paths) < 2:
            yield from self.anchors
        path_j = None
        for (path_i, path_j), level in zip(itertools.pairwise(reversed(self._anchor_paths)),
                                           reversed(self._ancestor_levels)):
            yield from path_i[:level:-1]
            yield from path_j[level:-1]
        if path_j is not None:
            yield path_j[-1]

    def __len__(self) -> int:
        p, l = self._anchor_paths, self._ancestor_levels
        if len(p) < 2:
            return len(p)
        return 1 + len(p[0]) + len(p[-1]) + 2 * (sum(map(len, p[1:-1])) - sum(l) - len(l))

    count = __len__

    @property
    def anchors(self):
        """View of the anchor nodes."""
        return [path[-1] for path in self._anchor_paths]

    @property
    def nodes(self):
        """View of all nodes that make up the route."""
        return self

    @property
    def edges(self):
        """View of all edges that make up the route."""
        return EdgesView(self)

    @property
    def lca(self) -> Optional[T]:
        try:
            i = min(self._ancestor_levels, default=0)
            return self._anchor_paths[0][i]
        except (IndexError, ValueError):
            return None  # Perhaps this is a bit dirty


class EdgesView:
    """View of edges of this route."""
    def __init__(self, route: Route):
        self._route = route

    def __iter__(self):
        return itertools.pairwise(self._route)

    def __reversed__(self):
        return ((x, y) for (y, x) in itertools.pairwise(reversed(self._route)))

    def __len__(self) -> int:
        n = len(self._route)
        if n > 0:
            return n - 1
        else:
            return 0

    count = __len__

def _common2(path_i, path_j) -> int:
    indices = range(min(len(path_i), len(path_j)))
    return bisect(indices, False, key=lambda ind: nid(path_i[ind]) != nid(path_j[ind])) - 1
