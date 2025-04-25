from abstracttree import print_tree, to_latex, to_image
from abstracttree.adapters import TreeAdapter, as_tree


def main():
    # Train a model
    from sklearn.datasets import load_iris
    from sklearn.model_selection import train_test_split
    from sklearn.tree import DecisionTreeClassifier
    iris = load_iris()
    X = iris.data
    y = iris.target
    X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=0)

    clf = DecisionTreeClassifier(max_leaf_nodes=3, random_state=0)
    model = clf.fit(X_train, y_train)

    # Now treat the model as a tree
    tree = convert_decisiontree(model)
    print_tree(tree)
    print(to_latex(tree, node_shape="rectangle", leaf_distance='8em', level_distance="10em"))
    to_image(tree, 'sklearn_example.png')


class DecisionTreeAdapter(TreeAdapter):
    @staticmethod
    def child_func(value):
        tree, idx = value
        lc, rc = tree.children_left[idx], tree.children_right[idx]
        if lc != -1:
            return (tree, lc), (tree, rc)
        else:
            return ()

    @property
    def feature(self):
        tree, idx = self.value
        return tree.feature[idx]

    @property
    def threshold(self):
        tree, idx = self.value
        return tree.threshold[idx]

    @property
    def result(self):
        tree, idx = self.value
        return tree.value[idx]

    @property
    def n_samples(self):
        tree, idx = self.value
        return tree.n_node_samples[idx]

    @property
    def impurity(self):
        tree, idx = self.value
        return tree.impurity[idx]

    def __str__(self):
        if self.children:
            text = f"if X[:, {self.feature}] ≤ {self.threshold:.4g}:  # {self.result}"
        else:
            text = f"return {self.value}"
        comment = f"# n_samples = {self.n_samples}, impurity = {self.impurity:.4g}"
        return comment + "\n" + text


def convert_decisiontree(model):
    tree = getattr(model, "tree_", model)
    return DecisionTreeAdapter((tree, 0))


if __name__ == '__main__':
    main()
