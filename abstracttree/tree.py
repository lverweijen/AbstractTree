import itertools
from abc import abstractmethod, ABCMeta
from collections import deque, namedtuple
from typing import TypeVar, Callable, Optional, Collection, Literal, \
    Iterable

TNode = TypeVar("TNode")
TMutDownNode = TypeVar("TMutDownNode", bound="MutableDownTree")
Order = Literal["pre", "post", "level"]
NodeItem = namedtuple("NodeItem", ["index", "depth"])
NodePredicate = Callable[[TNode, NodeItem], bool]


class AbstractTree(metaclass=ABCMeta):
    """Most abstract baseclass for everything."""
    __slots__ = ()

    @classmethod
    def convert(cls, obj):
        """Convert obj to tree-type or raise TypeError if that doesn't work."""
        from .adapters import convert_tree
        if isinstance(obj, cls):
            return obj
        tree = convert_tree(obj)
        if isinstance(tree, cls):
            return tree
        raise TypeError(f"{obj!r} cannot be converted to {cls.__name__}")

    @property
    def nid(self) -> int:
        """Unique number that represents this node."""
        return id(self)

    def eqv(self, other):
        """Check if both objects represent the same node.

        Should normally be operator.is, but can be overridden by delegates.
        """
        return self is other


class UpTree(AbstractTree, metaclass=ABCMeta):
    """Abstract class for tree classes with parent but no children."""
    __slots__ = ()

    @property
    @abstractmethod
    def parent(self: TNode) -> Optional[TNode]:
        """Parent of this node or None if root."""
        return None

    @property
    def is_root(self) -> bool:
        """Whether this node is a root (has no parent)."""
        return self.parent is None

    @property
    def root(self) -> TNode:
        """Root of tree."""
        p, p2 = self, self.parent
        while p2:
            p, p2 = p2, p2.parent
        return p

    @property
    def ancestors(self):
        """View of ancestors of node."""
        return AncestorsView(self.parent)

    @property
    def path(self):
        """View of path from root to node."""
        return PathView(self)


class DownTree(AbstractTree, metaclass=ABCMeta):
    """Abstract class for tree classes with children but no parent."""
    __slots__ = ()

    @property
    @abstractmethod
    def children(self: TNode) -> Collection[TNode]:
        """Children of this node."""
        return ()

    @property
    def leaves(self):
        """View of leaves from this node."""
        return LeavesView(self)

    @property
    def nodes(self):
        """View of this node and its descendants."""
        return NodesView([self], 0)

    @property
    def descendants(self):
        """View of descendants of this node."""
        return NodesView(self.children, 1)

    @property
    def levels(self):
        """View of this node and descendants by level."""
        return LevelsView(self)

    @property
    def is_leaf(self) -> bool:
        """Whether this node is a leaf (does not have children)."""
        return not self.children

    def transform(self: TNode, f: Callable[[TNode], TMutDownNode], keep=None) -> TMutDownNode:
        """Create new tree where each node of self is transformed by f."""
        stack = []
        for node, item in self.descendants.postorder(keep=keep):
            depth = item.depth
            while len(stack) < depth:
                stack.append(list())
            stack[depth - 1].append(new := f(node))
            if len(stack) > depth:
                new.add_children(stack.pop(-1))
        new = f(self)
        if stack:
            new.add_children(stack.pop())
        return new


class MutableDownTree(DownTree, metaclass=ABCMeta):
    """Abstract class for mutable tree with children."""
    __slots__ = ()

    @abstractmethod
    def add_child(self, node: TNode):
        """Add node to children."""
        raise NotImplementedError

    @abstractmethod
    def remove_child(self, node: TNode):
        """Remove node from children."""
        raise NotImplementedError

    def add_children(self, children: Iterable[TNode]):
        """Add multiple nodes to children."""
        for child in children:
            self.add_child(child)


class Tree(UpTree, DownTree, metaclass=ABCMeta):
    """Abstract class for tree classes with access to children and parents."""
    __slots__ = ()

    @property
    def siblings(self):
        """View of siblings of this node."""
        return SiblingsView(self)


class MutableTree(Tree, MutableDownTree, metaclass=ABCMeta):
    """Abstract class for mutable tree with children and parent."""
    __slots__ = ()

    def detach(self) -> TNode:
        """Remove parent if any and return self."""
        if p := self.parent:
            p.remove_child(self)
        return self


class TreeView(Iterable[TNode], metaclass=ABCMeta):
    __slots__ = ()

    def count(self) -> int:
        """Count number of nodes in this view."""
        counter = itertools.count()
        deque(zip(self, counter), maxlen=0)
        return next(counter)

    def __contains__(self, node) -> bool:
        return any(map(node.eqv, self))


class AncestorsView(TreeView):
    __slots__ = "parent"

    def __init__(self, parent):
        self.parent = parent

    def __iter__(self):
        p = self.parent
        while p:
            yield p
            p = p.parent

    def __bool__(self):
        return bool(self.parent)


class PathView(TreeView):
    __slots__ = "view"

    def __init__(self, node):
        self.view = AncestorsView(node)

    def __iter__(self):
        return reversed(list(self.view))

    def __reversed__(self):
        return iter(self.view)

    def __contains__(self, node):
        return node in self.view

    def __bool__(self):
        return True

    def count(self):
        return self.view.count()


class NodesView(TreeView):
    __slots__ = "nodes", "level"

    def __init__(self, nodes, level):
        self.nodes, self.level = nodes, level

    def __bool__(self):
        return bool(self.nodes)

    def __iter__(self):
        nodes = deque(self.nodes)
        while nodes:
            yield (node := nodes.pop())
            nodes.extend(node.children)

    def preorder(self, keep=None):
        """Iterate through nodes in pre-order.

        Only descend where keep(node).
        Returns tuples (node, item)
        Item denotes depth of iteration and index of child.
        """
        nodes = deque((c, NodeItem(i, self.level)) for (i, c) in enumerate(self.nodes))
        while nodes:
            node, item = nodes.popleft()
            if not keep or keep(node, item):
                yield node, item
                next_nodes = [(c, NodeItem(i, item.depth + 1))
                              for i, c in enumerate(node.children)]
                nodes.extendleft(reversed(next_nodes))

    def postorder(self, keep=None):
        """Iterate through nodes in post-order.

        Only descend where keep(node).
        Returns tuples (node, item)
        Item denotes depth of iteration and index of child.
        """
        children = iter([(c, NodeItem(i, self.level)) for (i, c) in enumerate(self.nodes)])
        node, item = next(children, (None, None))
        stack = []

        while node or stack:
            # Go down
            keep_node = keep is None or keep(node, item)
            while keep_node and node.children:
                stack.append((node, item, children))
                children = iter([(c, NodeItem(i, item.depth + 1))
                                 for (i, c) in enumerate(node.children)])
                node, item = next(children)
                keep_node = keep is None or keep(node, item)
            if keep_node:
                yield node, item

            # Go right or go up
            node, item = next(children, (None, None))
            while node is None and stack:
                node, item, children = stack.pop()
                yield node, item
                node, item = next(children, (None, None))

    def levelorder(self, keep=None):
        """Iterate through nodes in level-order.

        Only descend where keep(node).
        Returns tuples (node, item)
        Item denotes depth of iteration and index of child.
        """
        nodes = deque((c, NodeItem(i, self.level)) for (i, c) in enumerate(self.nodes))
        while nodes:
            node, item = nodes.popleft()
            if not keep or keep(node, item):
                yield node, item
                next_nodes = [(c, NodeItem(i, item.depth + 1))
                              for i, c in enumerate(node.children)]
                nodes.extend(next_nodes)


class LeavesView(TreeView):
    __slots__ = "root"

    def __init__(self, root):
        self.root = root

    def __bool__(self):
        return True

    def __iter__(self):
        for node in self.root.nodes:
            if node.is_leaf:
                yield node

    def __contains__(self, node):
        if not node.is_leaf:
            return False
        try:
            ancestors = node.ancestors
        except AttributeError:
            return node in super()
        else:
            return any(map(self.root.eqv, ancestors))


class LevelsView:
    __slots__ = "tree"

    def __init__(self, tree):
        self.tree = tree

    def __bool__(self):
        return True

    def __iter__(self):
        level = [self.tree]
        while level:
            yield iter(level)
            level = [child for node in level for child in node.children]

    def zigzag(self):
        """Traverse the levels in zigzag-order."""
        level = [self.tree]
        while level:
            yield iter(level)
            level = [child for node in reversed(level) for child in reversed(node.children)]

    def count(self):
        return 1 + max(it.depth for (_, it) in self.tree.nodes.preorder())


class SiblingsView(TreeView):
    __slots__ = "node"

    def __init__(self, node):
        self.node = node

    def __iter__(self):
        node = self.node
        parent = node.parent
        if parent is not None:
            return (child for child in parent.children if not node.eqv(child))
        else:
            return iter(())

    def __contains__(self, node):
        return not self.node.eqv(node) and self.node.parent.eqv(node.parent)

    def __len__(self):
        if p := self.node.parent:
            return len(p.children) - 1
        return 0

    count = __len__
