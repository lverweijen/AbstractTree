import abstracttree
import anytree


# If you want to use abstracttree as a mixin, it can be done like this.
# Usually the mixin would come second, but in this case anytree.Node has many similarly named methods and properties,
# which are already provided by abstracttree in a more generic way.
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
