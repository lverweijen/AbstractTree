from abstracttree.generics import DT, nid


def eqv(n1: DT, n2: DT) -> bool:
    """Whether two nodes are equivalent.

    For nodes to be equivalent, they need to have the same nid and be of the same type.
    The result is almost the same as ``n1 is n2``, but can be overridden for adapters, symlinks etc.
    """
    return nid(n1) == nid(n2) and type(n1) == type(n2)
