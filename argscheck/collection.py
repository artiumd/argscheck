"""
Collections
===========

This page documents checkers for collection objects.

We define a collection as a class that:

1. Implements `__len__()`.
2. Its instances are iterable.
3. Can be instantiated from an iterable.

Collections can be homogeneous, i.e. all items in it satisfy the same set of conditions.

Homogeneity can be checked for using by providing one or more positional arguments to the checker's constructor.
"""

from .core import check, Typed, Wrapper
from . import Comparable
from .numeric import Sized
from .iter import Iterable


class Collection(Sized, Typed):
    """
    Check if `x` is a (possible homogeneous) collection.

    :param args: *Optional[Tuple[CheckerLike]]* – If provided, apply the given check to each item in `x`.

    :Example:

    .. code-block:: python

        from argscheck import check, Collection


        # Check if a non-empty collection of floats
        checker = Collection(float, len_gt=0)

        check(checker, {1.2, 3.4})       # Passes, {1.2, 3.4} is returned
        check(checker, [1.1, 2.2, 3.3])  # Passes, [1.1, 2.2, 3.3] is returned
        check(checker, ())               # Fails, a ValueError is raised (empty collection)
        check(checker, 'abcd')           # Fails, a TypeError is raised (collection of str and not float)

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*self.types, **kwargs)

        if args:
            self.iterable = Iterable(*args)
        else:
            self.iterable = None

    def check(self, name, value, **kwargs):
        passed, value = super().check(name, value)
        if not passed:
            return False, value

        # If Collection was constructed with an empty *args, no need to iterate over items in the collection
        if self.iterable is None:
            return True, value

        if not name:
            name = repr(self).lower()

        items = list(check(self.iterable, value, name, **kwargs))

        for item in items:
            if isinstance(item, Wrapper):
                raise NotImplementedError(f'{self!r} does not does not support nesting deferred checkers.')

        try:
            value = type(value)(items)
        except TypeError:
            return False, TypeError(f'Failed on {type(value).__qualname__}(), make sure this type can be instantiated '
                                    f'from an iterable.')

        return True, value


class Set(Comparable, Collection, types=(set,)):
    """
    Check if `x` is a (possibly homogenous) `set` and optionally, check its length.

    `x` can also be compared to other sets using binary comparison operators, e.g. using `gt=other` will check if `x`
    is a superset of `other` (which must also be a `set`).

    Comparison shorthands can be used here, see example.

    :param args: *Optional[Tuple[CheckerLike]]* – If provided, apply the given check to each item in `x`.

    :Example:

    .. code-block:: python

        from argscheck import check, Set


        # Check if a set of length at least 2 and is a superset of {'a'}
        checker = Set(len_ge=2) > {'a'}

        check(checker, {'a', 'b'})    # Passes, {'a', 'b'} is returned
        check(checker, {'a', 1, ()})  # Passes, {'a', 1, ()} is returned
        check(checker, ['a', 'b'])    # Fails, a TypeError is raised (type is list and not set)
        check(checker, {'a'})         # Fails, a ValueError is raised (length is 1 and not 2 or greater)
        check(checker, {'b', 'c'})    # Fails, a ValueError is raised ({'b', 'c'} is not a superset of {'a'})

    :meta skip-extend-docstring-other_type:
    """

    def __init__(self, *args, **kwargs):
        # Sets should only be compared to other sets, hence: other_type=set
        self._assert_not_in_kwargs('other_type', **kwargs)
        super().__init__(*args, other_type=set, **kwargs)
