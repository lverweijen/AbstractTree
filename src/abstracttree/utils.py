from abstracttree.generics import DT, nid


def eqv(n1: DT, n2: DT) -> bool:
    """Whether 2 nodes reference the same object.

    Somewhat similar to is, but it also handles adapters, symlinks etc.
    """
    return nid(n1) == nid(n2) and type(n1) == type(n2)
