import os

abspath = os.path.abspath
pathjoin = os.path.join


def allf(fns, a):
    """Calls all `fns` with `a` and returns True if
    all are True
    """
    return all([fn(a) for fn in fns])


def reroot(name, srcdir=None, destdir=None):
    """Reroots the path `name` with a base directory
    relative to `srcdir` into `destdir`

    Essentially, joins `destdir` to the base described by
    (`name` - `srcdir`)
    """
    namebits = filter(None, name.split(os.path.sep))
    srcbits = filter(None, srcdir.split(os.path.sep))

    namebits.reverse()
    srcbits.reverse()

    while srcbits and namebits:
        srcbits.pop()
        namebits.pop()

    if srcbits:
        raise ValueError("name (%s) not contained within srcdir (%s)" % \
                             (name, srcdir))

    return pathjoin(destdir, os.path.sep.join(reversed(namebits)))
