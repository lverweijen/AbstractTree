import functools
import io
import operator
import subprocess
import sys
from pathlib import Path
from typing import Union, Callable, TypedDict, Tuple, Mapping, Any, TypeVar

from predicates import PreventCycles, MaxDepth
from treeclasses import DownTree, Tree

__all__ = [
    "print_tree",
    "plot_tree",
    "to_string",
    "to_dot",
    "to_mermaid",
    "to_image",
    "to_pillow",
    "LiteralText",
]

from conversions import astree


class Style(TypedDict):
    branch: str
    last: str
    vertical: str


DEFAULT_STYLES = {
    "square": Style(branch="├─", last="└─", vertical="│ "),
    "square-4": Style(branch="├──", last="└──", vertical="│  "),
    "square-arrow": Style(branch="├→", last="└→", vertical="│ "),
    "round": Style(branch="├─", last="╰─", vertical="│ "),
    "round-4": Style(branch="├──", last="╰──", vertical="│  "),
    "round-arrow": Style(branch="├→", last="╰→", vertical="│ "),
    "ascii": Style(branch="|--", last="`--", vertical="|  "),
    "ascii-arrow": Style(branch="|->", last="`->", vertical="|  "),
    "list": Style(branch="-", last="-", vertical=" "),
}


def _wrap_file(f):
    """Make sure file can be used in 3 ways:

    1) None (default) -> Return result as string
    2) str / path (filename) -> Write to filename
    3) Filebuffer -> Write to filebuffer
    """
    @functools.wraps(f)
    def new_f(tree, file=None, *args, **kwargs):
        if file is None:
            file = io.StringIO()
            f(tree, file=file, *args, **kwargs)
            return file.getvalue()
        elif not hasattr(file, "write"):
            with open(file, "w", encoding="utf-8") as writer:
                f(tree, writer, *args, **kwargs)
        else:
            f(tree, file=file, *args, **kwargs)

    return new_f


def print_tree(tree, formatter=str, style=None, keep=None):
    """Print this tree. Shortcut for print(to_string(tree))."""
    if sys.stdout:
        if not style:
            supports_unicode = not sys.stdout.encoding or sys.stdout.encoding.startswith("utf")
            style = "square" if supports_unicode else "ascii"
        return to_string(tree, file=sys.stdout, formatter=formatter, style=style, keep=keep)


@_wrap_file
def to_string(
    tree: DownTree, formatter=str, *, file=None, style: Union[str, Style] = "square", keep=None
):
    """Converts tree to a string in a pretty format."""
    tree = astree(tree)
    if isinstance(style, str):
        style = DEFAULT_STYLES[style]
    if keep is None:
        keep = PreventCycles()
    empty_style = len(style["last"]) * " "
    lookup1 = [empty_style, style["vertical"]]
    lookup2 = [style["last"], style["branch"]]

    for pattern, node in _iterate_patterns(tree, keep=keep):
        for i, line in enumerate(formatter(node).splitlines()):
            if node is not tree:
                if i == 0:
                    _write_indent(file, pattern, lookup1, lookup2)
                else:
                    _write_indent(file, pattern, lookup1, lookup1)
                file.write(" ")
            file.write(line)
            file.write("\n")


def _iterate_patterns(tree, keep):
    # Yield for each node a list of continuation indicators.
    # The continuation indicator tells us whether the branch at a certain level is continued.
    pattern = []
    yield pattern, tree
    for node, item in tree.descendants.preorder(keep=keep):
        del pattern[item.depth - 1 :]
        is_continued = item.index < len(node.parent.children) - 1
        pattern.append(is_continued)
        yield pattern, node


def _write_indent(file, pattern, lookup1, lookup2):
    # Based on calculated patterns, this will substitute an indent line
    if pattern:
        for is_continued in pattern[:-1]:
            file.write(lookup1[is_continued])
            file.write(" ")
        file.write(lookup2[pattern[-1]])


def plot_tree(tree: Tree, ax=None, formatter=str, maxdepth=5, annotate_args=None):
    """Plot the tree using matplotlib (if installed)."""
    # Roughly based on sklearn.tree.plot_tree()
    import matplotlib.pyplot as plt
    tree = astree(tree)

    if ax is None:
        ax = plt.gca()

    ax.clear()
    ax.set_axis_off()

    kwargs = dict(
        ha="center",
        va="center",
        arrowprops={"arrowstyle": "<-"},
        xycoords="axes fraction",
        bbox={"fc": ax.get_facecolor()},
    )
    if annotate_args:
        kwargs.update(annotate_args)

    nodes_xy = {}

    keep = MaxDepth(maxdepth) if maxdepth else PreventCycles()
    tree_height = max(it.depth for _, it in tree.descendants.preorder(keep=keep))

    for depth, level in zip(range(tree_height), tree.levels):
        level = list(level)
        for i, node in enumerate(level):
            x = (i + 1) / (len(level) + 1)
            y = 1 - depth / tree_height
            kwargs['zorder'] = 100 - 10 * depth
            if node is tree:
                ax.annotate(formatter(node), (x, y), **kwargs)
            else:
                parent = nodes_xy[node.parent.nid]
                ax.annotate(formatter(node), parent, (x, y), **kwargs)
            nodes_xy[node.nid] = x, y
    return ax


TNode = TypeVar("TNode", bound=DownTree)
TShape = Union[Tuple[str, str], str, Callable[[TNode], Union[Tuple[str, str], str]]]
NodeAttributes = Union[Mapping[str, Any], Callable[[TNode], Mapping[str, Any]]]
EdgeAttributes = Union[Mapping[str, Any], Callable[[TNode, TNode], Mapping[str, Any]]]
GraphAttributes = Mapping[str, Any]


def to_image(
    tree: Tree,
    file=None,
    how="dot",
    *args,
    **kwargs,
):
    """Export to image. Uses graphviz(dot) or mermaid."""
    if how == "dot":
        if file is None:
            img = _image_dot(tree, file=subprocess.PIPE, file_format="png", *args, **kwargs)
            return io.BytesIO(img)
        elif hasattr(file, "write"):
            _image_dot(tree, file, file_format="png", *args, **kwargs)
        else:
            filepath = Path(file)
            with open(filepath, "bw") as file:
                _image_dot(tree, file, file_format=filepath.suffix[1:], *args, **kwargs)
    elif how == "mermaid":
        _image_mermaid(tree, Path(file), *args, **kwargs)


def to_pillow(tree: Tree, **kwargs):
    from PIL import Image
    return Image.open(to_image(tree, file=None, how="dot", **kwargs))


def _image_dot(
    tree: Tree,
    file=None,
    file_format="png",
    program_path="dot",
    **kwargs,
):
    args = [str(program_path), "-T", file_format]
    process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=file, stderr=subprocess.PIPE)
    to_dot(tree, file=io.TextIOWrapper(process.stdin, encoding="utf-8"), **kwargs)
    process.stdin.close()
    (output, errors) = process.communicate()
    if process.returncode != 0:
        raise Exception(errors.decode("utf-8", errors="replace"))
    return output


def _image_mermaid(
    tree: Tree,
    filename,
    program_path="mmdc",
    **kwargs,
):
    args = [str(program_path), "--input", "-", "--output", str(filename)]
    process = subprocess.Popen(args, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    to_mermaid(tree, file=io.TextIOWrapper(process.stdin, encoding="utf-8"), **kwargs)
    process.stdin.close()
    (output, errors) = process.communicate()
    if process.returncode != 0:
        raise Exception(errors.decode("utf-8", errors="replace"))
    return output


@_wrap_file
def to_dot(
    tree: Tree,
    file=None,
    keep=None,
    node_name: Union[str, Callable[[TNode], str], None] = None,
    node_label: Union[str, Callable[[TNode], str], None] = str,
    node_shape: TShape = None,
    node_attributes: NodeAttributes = None,
    edge_attributes: EdgeAttributes = None,
    graph_attributes: GraphAttributes = None,
):
    """Export to graphviz.

    See https://graphviz.org/
    """
    tree = astree(tree)
    if node_name is None:
        node_name = _node_name_default

    if keep is None:
        keep = PreventCycles()

    if node_attributes is None:
        node_attributes = dict()
    else:
        node_attributes = dict(node_attributes)

    edge_attributes = edge_attributes or dict()
    graph_attributes = graph_attributes or dict()

    if node_label and "label" not in node_attributes:
        node_attributes["label"] = _makecallable(node_label)
    if node_shape and "shape" not in node_attributes:
        node_attributes["shape"] = node_shape

    node_static, node_dynamic = _split_attributes(node_attributes)
    edge_static, edge_dynamic = _split_attributes(edge_attributes)

    arrow = "->"
    file.write("strict digraph tree {\n")

    if graph_attributes:
        attrs = _handle_attributes(graph_attributes, tree)
        file.write(f"graph{attrs};\n")
    if node_static:
        attrs = _handle_attributes(node_static, tree)
        file.write(f"node{attrs};\n")
    if edge_static:
        attrs = _handle_attributes(edge_static, tree, tree)
        file.write(f"edge{attrs};\n")

    nodes = []
    for node, _ in tree.nodes.preorder(keep=keep):
        nodes.append(node)
        name = _escape_string(node_name(node), "dot")
        attrs = _handle_attributes(node_dynamic, node)
        file.write(f"{name}{attrs};\n")
    nodes = iter(nodes)
    next(nodes)
    for node in nodes:
        parent_name = _escape_string(node_name(node.parent), "dot")
        child_name = _escape_string(node_name(node), "dot")
        attrs = _handle_attributes(edge_dynamic, node.parent, node)
        file.write(f"{parent_name}{arrow}{child_name}{attrs};\n")
    file.write("}\n")


def _split_attributes(attributes: Union[NodeAttributes, EdgeAttributes]):
    static = {k: v for (k, v) in attributes.items() if not callable(v)}
    dynamic = {k: v for (k, v) in attributes.items() if callable(v)}
    return static, dynamic


def _handle_attributes(attributes, *args):
    res = []
    for k, v in attributes.items():
        if callable(v):
            v = v(*args)
        res.append(f"{k}={_escape_string(v, 'dot')}")
    if res:
        return '[' + "".join(res) + ']'
    else:
        return ""


DEFAULT_SHAPES = {
    "box": ("[", "]"),
    "rectangle": ("[", "]"),
    "round": ("(", ")"),
    "stadium": ("([", "])"),
    "subroutine": ("[[", "]]"),
    "asymmetric": (">", "]"),
    "circle": ("((", "))"),
    "double-circle": ("(((", ")))"),
    "doublecircle": ("(((", ")))"),
    "rhombus": ("{", "}"),
    "hexagon": ("{{", "}}"),
    "parallelogram": ("[/", "/]"),
    "inv-parallelogram": ("[\\", r"\]"),
    "invparallelogram": ("[\\", r"\]"),
    "trapezium": ("[/", r"\]"),
    "inv-trapezium": ("[\\", "/]"),
}


@_wrap_file
def to_mermaid(
    tree: Tree,
    file=None,
    keep=None,
    node_name: Union[str, Callable[[TNode], str], None] = None,
    node_label: Union[str, Callable[[TNode], str], None] = str,
    node_shape: TShape = "box",
    edge_arrow: Union[str, Callable[[TNode, TNode], str]] = "-->",
    graph_direction: str = "TD",
):
    """Export to mermaid diagram.

    See https://mermaid.js.org/
    """
    tree = astree(tree)
    if node_name is None:
        node_name = _node_name_default

    if isinstance(node_shape, str):
        node_shape = DEFAULT_SHAPES[node_shape]

    if keep is None:
        keep = PreventCycles()

    # Output header
    file.write(f"graph {graph_direction};\n")

    # Output nodes
    nodes = []  # Stop automatic garbage collecting
    for node, _ in tree.nodes.preorder(keep=keep):
        left, right = _get_shape(node_shape, node)
        name = node_name(node)
        if node_label:
            text = _escape_string(node_label(node), "mermaid")
            file.write(f"{name}{left}{text}{right};\n")
        else:
            file.write(f"{name};\n")
        nodes.append(node)

    # Output edges
    nodes = iter(nodes)
    next(nodes)
    for node in nodes:
        arrow = edge_arrow(node.parent, node) if callable(edge_arrow) else edge_arrow
        parent = node_name(node.parent)
        child = node_name(node)
        file.write(f"{parent}{arrow}{child};\n")


def _node_name_default(node: DownTree):
    return hex(node.nid)


def _get_shape(shape_factory, node):
    if callable(shape_factory):
        shape = shape_factory(node)
        if isinstance(shape, str):
            shape = DEFAULT_SHAPES[shape]
    else:
        shape = shape_factory
    return shape


def _makecallable(f):
    if isinstance(f, str):
        f = operator.attrgetter(f)
    return f


def _escape_string(text, what) -> str:
    if isinstance(text, LiteralText):
        return text

    text = str(text)
    if what == "dot":
        text = '"' + text.replace('"', '\\"') + '"'
    elif what == "mermaid":
        text = text.replace("#", "#35;")
        text = text.replace("`", "#96;")
        text = text.replace('"', "#quot;")
    return text


class LiteralText(str):
    pass
