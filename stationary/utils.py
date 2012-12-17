

def allf(fns, a):
    """Calls all `fns` with `a` and returns True if
    all are True
    """
    return all([fn(a) for fn in fns])

