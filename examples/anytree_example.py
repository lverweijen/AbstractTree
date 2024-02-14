import abstracttree
import anytree


# This works for combining both
class MyTree(abstracttree.Tree, anytree.Node):
    children = anytree.NodeMixin.children
    parent = anytree.NodeMixin.parent


tree = MyTree('<root>')
tree.children = list(map(MyTree, [1, 2, 3, 4, 5]))

# Usage in the style of abstracttree
print("# AbstractTree #")
for node, item in tree.nodes.preorder():
    print("node.name = {!r}".format(node.name))

abstracttree.print_tree(tree)
print()

# Usage in the style of anytree
print("# AnyTree #")
for node in anytree.PreOrderIter(tree):
    print("node.name = {!r}".format(node.name))

print(anytree.RenderTree(tree).by_attr(str))
print()
