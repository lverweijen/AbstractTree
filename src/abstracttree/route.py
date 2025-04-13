import itertools
from abc import ABCMeta
from bisect import bisect
from collections.abc import Sized, Sequence, MutableSequence
from functools import lru_cache
from typing import TypeVar, Optional

from . import _iterators
from .generics import TreeLike, eqv

TNode = TypeVar("TNode", bound=TreeLike)


class Route:
    """Representation of a route trough adjacent nodes in the tree.

    Two nodes are adjacent if they have a parent-child relationship.
    The route will be as short as possible, but it will visit the anchor points in order.
    """

    __slots__ = "_apaths", "_lca"

    def __init__(self, *anchors: TreeLike):
        """Create a route through a few nodes.

        All nodes should belong to the same tree.
        """
        self._apaths: MutableSequence[Sequence[TNode]] = []
        self._lca = None

        for anchor in anchors:
            self.add_anchor(anchor)

    def __repr__(self):
        nodes_str = ", ".join([repr(p[-1]) for p in self._apaths])
        return f"{self.__class__.__name__}({nodes_str})"

    def add_anchor(self, anchor: TreeLike):
        """Add a node to the route.

        The node should belong to the same tree as any existing anchor nodes.
        """
        self._lca = None
        anchor_ancestors = list(_iterators.ancestors(anchor))
        anchor_path = list(itertools.chain(reversed(anchor_ancestors), [anchor]))

        apaths = self._apaths

        if apaths and not eqv(apaths[0][0], anchor_path[0]):
            raise ValueError("Different tree!")
        else:
            apaths.append(anchor_path)

    @property
    def anchors(self):
        """View of the anchor nodes."""
        return AnchorsView(self, self._apaths)

    @property
    def nodes(self):
        """View of all nodes that make up the route."""
        return NodesView(self, self._apaths)

    @property
    def edges(self):
        """View of all edges that make up the route."""
        return EdgesView(self, self._apaths)

    @property
    def lca(self) -> Optional[TNode]:
        """The least common ancestor of all anchor nodes."""
        paths = self._apaths
        path0 = min(paths, key=len)
        indices = range(len(path0))
        if i := bisect(
            indices,
            False,
            key=lambda ind: any(not eqv(path0[ind], p[ind]) for p in paths),
        ):
            lca = self._lca = path0[i - 1]
            return lca
        else:
            return None

    @lru_cache
    def _common2(self, i, j) -> int:
        path_i, path_j = self._apaths[i], self._apaths[j]
        indices = range(min(len(path_i), len(path_j)))
        return bisect(indices, False, key=lambda ind: not eqv(path_i[ind], path_j[ind])) - 1


class RouteView(Sized, metaclass=ABCMeta):
    def __init__(self, route, apaths):
        self._route = route
        self._apaths = apaths

    def count(self):
        # Counting takes logarithmic time, so we define len in subclasses
        return len(self)


class AnchorsView(RouteView):
    def __len__(self):
        return len(self._apaths)

    def __getitem__(self, item):
        return self._apaths[item][-1]


class NodesView(RouteView):
    def __iter__(self):
        indices = range(len(self._apaths))
        path_j = None
        for i, j in itertools.pairwise(indices):
            path_i, path_j = self._apaths[i : j + 1]
            c = self._route._common2(i, j)
            yield from path_i[:c:-1] + path_j[c:-1]
        if path_j:
            yield path_j[-1]

    def __reversed__(self):
        indices = range(len(self._apaths))
        path_i = None
        for j, i in itertools.pairwise(indices[::-1]):
            path_i, path_j = self._apaths[i : j + 1]
            c = self._route._common2(i, j)
            yield from path_j[:c:-1] + path_i[c:-1]
        if path_i:
            yield path_i[-1]

    def __len__(self):
        s = 1
        indices = range(len(self._apaths))
        for i, j in itertools.pairwise(indices):
            p1, p2 = self._apaths[i : j + 1]
            s += len(p1) + len(p2) - 2 * self._route._common2(i, j) - 2
        return s


class EdgesView(RouteView):
    def __iter__(self):
        return itertools.pairwise(self._route.nodes)

    def __reversed__(self):
        return itertools.pairwise(reversed(self._route.nodes))

    def __len__(self):
        return len(self._route.nodes) - 1
