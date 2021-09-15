"""
Collections
===========
"""
from .core import Typed, Comparable
from .numeric import Sized
from .iter import Iterable


class Collection(Sized, Typed):
    """
    Check if argument is a homogenous collection, i.e. each item in the collection satisfies the same set of checkers.

    A collection is assumed to have the following properties:

    1. Has ``__len__()`` implemented.
    2. Is iterable.
    3. Can be instantiated from an iterable.

    :param args: *Tuple[CheckerLike]* – Describes what each item in the collection must be.
    """
    types = (object,)

    def __init__(self, *args, **kwargs):
        # TODO add `astype=None` option
        super().__init__(*self.types, **kwargs)

        if args:
            self.iterable = Iterable(*args)
        else:
            self.iterable = None

    def __call__(self, name, value):
        passed, value = super().__call__(name, value)
        if not passed:
            return False, value

        # If Collection was constructed with an empty *args, no need to iterate over items in the collection
        if self.iterable is None:
            return True, value

        # Determine returned collection type
        type_ = type(value)

        # Create returned collection, any item yielded by the iterable that fails the check will raise an error
        try:
            value = type_(self.iterable(name, value))

            return True, value
        except Exception as e:
            return False, e


class Set(Comparable, Collection):
    """
    Check if argument is a homogenous ``set`` and optionally, check its length and compare it to other sets using binary
    operators, e.g. using ``gt`` will check if argument is a superset of the other set.

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
    """
    types = (set,)

    def __init__(self, *args, **kwargs):
        # Sets should only be compared to other sets, hence: other_type=set
        super().__init__(*args, other_type=set, **kwargs)
