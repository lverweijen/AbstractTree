# Changelog

## Version 0.2.1

* Improve and simplify Route:
  * Handle edge-cases correctly, especially when dealing with 1 of 0 anchors.
    These used to return incorrect values for e.g. `route.count()`.
  * Merge `Route` and `NodesView` classes.
  * Make anchors return a `tuple` instead of an `AnchorView`.
  * Make `reversed(route.edges)` return edges in parent-child order for consistency with `iter(route.edges)`.
    In prior versions, `reversed(path)` would return edges in child-parent order.
* Implement `path.edges` as well to make `path` more `routelike`.
* Implement `path.to` as a shortcut to create a `Route` by writing `route = node.path.to(other_node)`.

## Version 0.2.0

* Add generics `TreeLike` and `DownTreeLike`.
* Add many new functions that accept above generics as parameter.
* Change many existing functions to accept above generics above as parameter.
* Rename `astree(x)` to `as_tree(x)`. Also `as_tree` will now always return a `TreeView`.
* Remove `convert_tree.register`, but add granular methods `children.register`, `parent.register`.
* Iteration methods on `tree.nodes` and `tree.descendants` now use `None` as index for root (instead of 0).
* Change how `Mapping` is converted to Tree. `children(mapping)` is mostly similar to `mapping.items()`. This works well on jsonlike-data.
* Replace `x.eqv(y)` method by `eqv(x, y)` function.
* `TreeAdapter` remains, but some alternative adapters have been removed.
* `TreeAdapter` is hashable if the underlying object is hashable.
* `TreeAdapter.node` has been renamed to `TreeAdapter.value`.
* `HeapTree` has become immutable and hashable (by id(heap) and index). The heap itself may remain mutable without a problem.

## Version 0.1.1

* Make it possible to pass options like `file_format` to `to_image`.
* `to_image` returns bytes if no filename is given, not bytesIO.
* Add function `to_reportlab`. This requires [svglib](https://pypi.org/project/svglib/) to be installed.
* Classes can define `_abstracttree_` to override their conversion to tree.

## Version 0.1.0

* `UpTree` is no longer exported by default, although it can still be imported.
  It has been removed from the documentation and is considered for deletion.
* Add `AbstractTree.convert(obj)` as a type-aware replacement for `astree(obj)`.
  For instance, `DownTree.convert(obj)` can be used if `obj.parent` doesn't exist.
* Rename `treeclasses.py` to `tree.py`
* Rename `conversions.py` to `adapters.py`
* Don't special-case `x in node.ancestors` to use identity comparison.
* `to_dot` and `to_mermaid` now generate nodes in levelorder (breadth first), instead of preorder (depth-first)

## Version 0.0.5

* Add `reversed(Route(node_1 ... node_n).edges)` to walk through nodes backwards.
* Add `BinaryTree` and `BinaryDownTree` abstract classes.
* Add `tree.levels.zigzag()` method to iterate through levels in [zigzag-order](https://www.geeksforgeeks.org/zigzag-tree-traversal/).
