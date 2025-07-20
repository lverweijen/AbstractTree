import functools
import io
import itertools
import operator
import subprocess
import sys
from collections.abc import Iterable, Mapping, Callable
from pathlib import Path
from typing import Union, TypedDict, Tuple, Any, TypeVar, Optional

from . import generics
from .iterators import preorder, levels, levelorder
from .adapters import convert_tree
from .generics import TreeLike, DownTreeLike, label, nid
from .predicates import PreventCycles, MaxDepth

__all__ = [
    "print_tree",
    "plot_tree",
    "to_string",
    "to_dot",
    "to_mermaid",
    "to_image",
    "to_pillow",
    "to_latex",
    "to_reportlab",
    "LiteralText",
]


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

# By default, all exporters are limited to a depth of 5.
DEFAULT_PREDICATE = MaxDepth(5)


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


def print_tree(tree, formatter=generics.label, style=None, keep=None):
    """Print this tree. Shortcut for print(to_string(tree))."""
    if sys.stdout:
        if not style:
            supports_unicode = not sys.stdout.encoding or sys.stdout.encoding.startswith("utf")
            style = "square" if supports_unicode else "ascii"
        return to_string(tree, file=sys.stdout, formatter=formatter, style=style, keep=keep)


@_wrap_file
def to_string(
    tree: DownTreeLike,
    formatter: Callable[[object], str] | str | None = generics.label,
    *,
    file=None,
    style: Union[str, Style] = "square",
    keep=None,
):
    """Converts tree to a string in a pretty format."""
    tree = convert_tree(tree, TreeLike)
    if isinstance(style, str):
        style = DEFAULT_STYLES[style]
    if formatter is None:
        formatter = generics.label
    elif isinstance(formatter, str):
        formatter = formatter.format
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
    _children = generics.children.dispatch(type(tree))
    _parent = generics.parent.dispatch(type(tree))

    pattern = []
    yield pattern, tree
    for node, item in preorder(tree, keep=keep, include_root=False):
        del pattern[item.depth - 1 :]
        is_continued = item.index < len(_children(_parent(node))) - 1
        pattern.append(is_continued)
        yield pattern, node


def _write_indent(file, pattern, lookup1, lookup2):
    # Based on calculated patterns, this will substitute an indent line
    if pattern:
        for is_continued in pattern[:-1]:
            file.write(lookup1[is_continued])
            file.write(" ")
        file.write(lookup2[pattern[-1]])


def plot_tree(
    tree: DownTreeLike,
    ax=None,
    formatter: Callable[[DownTreeLike], str] | str = label,
    keep=DEFAULT_PREDICATE,
    annotate_args=None
):
    """Plot the tree using matplotlib (if installed)."""
    # Roughly based on sklearn.tree.plot_tree()
    import matplotlib.pyplot as plt

    tree = convert_tree(tree, TreeLike)
    if isinstance(formatter, str):
        formatter = formatter.format

    _parent = generics.parent.dispatch(type(tree))

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

    tree_height = max(it.depth for _, it in preorder(tree, keep=keep, include_root=False))
    for depth, level in zip(range(tree_height + 1), levels(tree)):
        level = list(level)
        for i, node in enumerate(level):
            x = (i + 1) / (len(level) + 1)
            y = 1 - depth / tree_height
            kwargs["zorder"] = 100 - 10 * depth
            if node is tree:
                ax.annotate(formatter(node), (x, y), **kwargs)
            else:
                p_node = nodes_xy[nid(_parent(node))]
                ax.annotate(formatter(node), p_node, (x, y), **kwargs)
            nodes_xy[nid(node)] = x, y
    return ax


TNode = TypeVar("TNode", bound=DownTreeLike)
TShape = Union[Tuple[str, str], str, Callable[[TNode], Union[Tuple[str, str], str]]]
NodeAttributes = Union[Mapping[str, Any], Callable[[TNode], Mapping[str, Any]]]
EdgeAttributes = Union[Mapping[str, Any], Callable[[TNode, TNode], Mapping[str, Any]]]
GraphAttributes = Mapping[str, Any]


def to_image(
    tree: DownTreeLike,
    file=None,
    how="dot",
    *args,
    **kwargs,
):
    """Export to image. Uses graphviz(dot) or mermaid.

    If file is str or Path, save file under given name.
    If file is None (default), return image as bytes.
    If file is writable (binary), write to it.
    """
    if how == "dot":
        if file is None:
            return _image_dot(tree, file=subprocess.PIPE, *args, **kwargs)
        elif hasattr(file, "write"):
            _image_dot(tree, file, *args, **kwargs)
        else:
            filepath = Path(file)
            if "file_format" not in kwargs:
                kwargs = kwargs.copy()
                kwargs.setdefault("file_format", filepath.suffix[1:])
            with open(filepath, "bw") as file:
                _image_dot(tree, file, *args, **kwargs)
    elif how == "mermaid":
        _image_mermaid(tree, Path(file), *args, **kwargs)


def to_pillow(tree: DownTreeLike, **kwargs):
    """Convert tree to pillow-format (uses graphviz on the background)."""
    from PIL import Image

    if "file_format" not in kwargs:
        kwargs = kwargs.copy()
        kwargs.setdefault("file_format", "png")
    return Image.open(io.BytesIO(to_image(tree, file=None, how="dot", **kwargs)))


def to_reportlab(tree: DownTreeLike, **kwargs):
    """Convert tree to drawing for use with reportlab package."""
    from svglib.svglib import svg2rlg

    if "file_format" not in kwargs:
        kwargs = kwargs.copy()
        kwargs.setdefault("file_format", "svg")
    svg_bytes = to_image(tree, **kwargs)
    drawing = svg2rlg(io.BytesIO(svg_bytes))
    return drawing


def _image_dot(
    tree: DownTreeLike,
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
    tree: DownTreeLike,
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
    tree: DownTreeLike,
    file=None,
    keep=DEFAULT_PREDICATE,
    node_name: Union[str, Callable[[TNode], str], None] = None,
    node_label: Union[str, Callable[[TNode], str], None] = generics.label,
    node_shape: TShape = None,
    node_attributes: NodeAttributes = None,
    edge_attributes: EdgeAttributes = None,
    graph_attributes: GraphAttributes = None,
):
    """Export to `graphviz <https://graphviz.org/>`_."""
    tree = convert_tree(tree, TreeLike)
    if node_name is None:
        node_name = _node_name_default

    _parent = generics.parent.dispatch(type(tree))

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
    for node, _ in levelorder(tree, keep=PreventCycles() & keep):
        nodes.append(node)
        name = _escape_string(node_name(node), "dot")
        attrs = _handle_attributes(node_dynamic, node)
        file.write(f"{name}{attrs};\n")
    nodes = iter(nodes)
    next(nodes)
    for node in nodes:
        parent_name = _escape_string(node_name(_parent(node)), "dot")
        child_name = _escape_string(node_name(node), "dot")
        attrs = _handle_attributes(edge_dynamic, _parent(node), node)
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
        return "[" + "".join(res) + "]"
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
    tree: DownTreeLike,
    file=None,
    keep=DEFAULT_PREDICATE,
    node_name: Union[str, Callable[[TNode], str], None] = None,
    node_label: Union[str, Callable[[TNode], str], None] = generics.label,
    node_shape: TShape = "box",
    edge_arrow: Union[str, Callable[[TNode, TNode], str]] = "-->",
    graph_direction: str = "TD",
):
    """Export to `mermaid <https://mermaid.js.org/>`_."""
    tree = convert_tree(tree, TreeLike)
    if node_name is None:
        node_name = _node_name_default

    _parent = generics.parent.dispatch(type(tree))

    if isinstance(node_shape, str):
        node_shape = DEFAULT_SHAPES[node_shape]

    # Output header
    file.write(f"graph {graph_direction};\n")

    # Output nodes
    nodes = []  # Stop automatic garbage collecting
    for node, _ in levelorder(tree, keep=PreventCycles() & keep):
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
        arrow = edge_arrow(_parent(node), node) if callable(edge_arrow) else edge_arrow
        par = node_name(_parent(node))
        child = node_name(node)
        file.write(f"{par}{arrow}{child};\n")


@_wrap_file
def to_latex(
    tree: DownTreeLike,
    file=None,
    keep=DEFAULT_PREDICATE,
    node_label: Union[str, Callable[[TNode], str], None] = generics.label,
    node_shape: TShape = None,
    leaf_distance: Optional[str] = "2em",
    level_distance: Optional[str] = None,
    node_options: Iterable[Union[str, Callable[[TNode], str]]] = (),
    picture_options: Iterable[Union[str, Callable[[TNode], str]]] = (),
    graph_direction: str = "right",
    indent: Union[str, int] = 4,
    align="center",
):
    """Export to latex (experimental).

    Make sure to put ``\\usepackage{tikz}`` in your preamble.
    Does not wrap output in a figure environment.
    """
    if isinstance(indent, int):
        indent = "\t" if indent == -1 else indent * " "

    picture_options = list(picture_options)
    if align is not None:
        picture_options.append(f"align={align}")
    if leaf_distance:
        distances = _sibling_distances(tree)
        for level in range(1, len(distances)):
            sibling_distance = f"{distances[level]:g}*{leaf_distance}"
            option = f"\nlevel {level}/.style = {{sibling distance = {sibling_distance}}}"
            picture_options.append(option)
    if level_distance:
        picture_options.append(f"level distance = {level_distance}")
    node_options = list(node_options)
    if node_shape:
        node_options.append(node_shape)
        node_options.append("draw")

    depth = 0
    my_label = _escape_string(node_label(tree), "latex")
    file.write(rf"\begin{{tikzpicture}}{_latex_options(tree, picture_options)}")
    file.write("\n")
    options = _latex_options(tree, node_options)
    file.write(rf"\node{options}{{{my_label}}} [grow={graph_direction}]")
    for node, item in preorder(tree, keep=keep, include_root=False):
        if item.depth > depth:
            file.write("\n")
        else:
            file.write("}\n")
            for back in range(depth - 1, item.depth - 1, -1):
                file.write(back * indent + "}\n")

        depth = item.depth
        file.write(depth * indent)
        text = _escape_string(node_label(node), "latex")
        options = _latex_options(tree, node_options)
        file.write(f"child {{node{options} {{{text}}}")

    # Close final leaf node on same line
    if depth:
        depth -= 1
        file.write("}")

    # Close open nodes
    file.write("\n")
    for back in range(depth, 0, -1):
        file.write(back * indent + "}\n")

    file.write(r"\end{tikzpicture}")


def _latex_options(node, options):
    output = []
    for option in options:
        if callable(option):
            output.append(str(option(node)))
        else:
            output.append(str(option))
    if not output:
        return ""
    else:
        joined = ",".join(output)
        return f"[{joined}]"


def _sibling_distances(tree, stop=100):
    """Calculate sibling distances in such a way that nodes don't overlap.

    The chosen strategy is to multiply level ranks from bottom to top.
    It assumes sibling distance is constant for each level.
    Parameter stop is used to prevent infinite recursion.
    """
    _children = generics.children.dispatch(type(tree))

    level_ranks = []
    for level, _ in zip(levels(tree), range(stop)):
        cousins = itertools.pairwise(level)
        mid_ranks = [(len(_children(n1)) + len(_children(n2))) / 2 for n1, n2 in cousins]
        level_ranks.append(max(max(mid_ranks), 1) if mid_ranks else 1)

    distances = len(level_ranks) * [1]
    for level in reversed(range(len(level_ranks) - 1)):
        distances[level] = level_ranks[level] * distances[level + 1]
    return distances


def _node_name_default(node: Any):
    return hex(nid(node))


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
    elif what == "latex":
        text = text.replace("\\", r"\textbackslash")
        special_chars = "#$%&_{}"
        for char in special_chars:
            text = text.replace(char, f"\\{char}")

        text = text.replace("~", r"\~{}")
        text = text.replace("^", r"\^{}")
        text = text.replace("\n", r"\\")
    return text


class LiteralText(str):
    pass
