# Changelog

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
