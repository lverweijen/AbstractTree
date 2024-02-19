"""
itertree (https://pypi.org/project/itertree/) is a fast genericic tree implementation
It can be used with abstracttree as shown in the code below.

Note that subclassing iTree is still a bit tricky.
This has been pointed out on https://github.com/BR1py/itertree/issues/30
In particular, avoid doing tree.append(5). Always use tree.append(MyTree(5)) instead.
"""


import itertree

import abstracttree
from abstracttree import print_tree


class MyTree(itertree.iTree, abstracttree.Tree):
    __slots__ = ()

    @property
    def children(self):
        return self

    def __str__(self):
        # Don't print subtrees
        only_self = lambda n: n is self
        return self.renders(filter_method=only_self)


tree = MyTree(1)

node = tree
for i in range(7):
    node.append(child := MyTree(i))
    node = child

# AbstractTree
print("Height of tree:", tree.levels.count() - 1)
print_tree(tree)

# iTree
print("Height of tree:", tree.max_depth)
tree.render()
