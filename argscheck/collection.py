"""
Collections
===========

This module contains checkers for collection objects.

In this context, a collection is a class that:

1. Has ``__len__()`` implemented.
2. Its instances are iterable.
3. Can be instantiated from an iterable.

Collections can be homogeneous, i.e. all items in it have some shared properties. Homogeneity can be checked using the
``*args`` parameter.
"""
from .core import check, Typed, Comparable, Wrapper
from .numeric import Sized
from .iter import Iterable


class Collection(Sized, Typed):
    """
    Check if ``x`` is a collection.

    :param args: *Optional[Tuple[CheckerLike]]* – If provided, this check will be applied to each item in ``x``.

    :Example:

    .. code-block:: python

        from argscheck import Collection

        # Check if a non empty collection of floats
        checker = Collection(float, len_gt=0)

        checker.check({1.2, 3.4})       # Passes, returns {1.2, 3.4}
        checker.check([1.1, 2.2, 3.3])  # Passes, returns [1.1, 2.2, 3.3]
        checker.check(())               # Fails, raises ValueError (empty collection)
        checker.check('abcd')           # Fails, raises TypeError (collection of str and not float)

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
    Check if ``x`` is a homogenous ``set`` and optionally, check its length and compare it to other sets using binary
    operators, e.g. using ``gt=other`` will check if ``x`` is a superset of ``other`` (which must also be a ``set``).

    :param args: *Optional[Tuple[CheckerLike]]* – If provided, this check will be applied to each item in ``x``.

    :Example:

    .. code-block:: python

        from argscheck import Set

        # Check if a set of length at least 2 and is a superset of {'a'}
        checker = Set(gt={'a'}, len_ge=2)

        checker.check({'a', 'b'})    # Passes, returns {'a', 'b'}
        checker.check({'a', 1, ()})  # Passes, returns {'a', 1, ()}
        checker.check(['a', 'b'])    # Fails, raises TypeError (type is list and not set)
        checker.check({'a'})         # Fails, raises ValueError (length is 1 and not 2 or greater)
        checker.check({'b', 'c'})    # Fails, raises ValueError ({'b', 'c'} is not a superset of {'a'})

    :meta skip-extend-docstring-other_type:
    """

    def __init__(self, *args, **kwargs):
        # Sets should only be compared to other sets, hence: other_type=set
        self._assert_not_in_kwargs('other_type', **kwargs)
        super().__init__(*args, other_type=set, **kwargs)
