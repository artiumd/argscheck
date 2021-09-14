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
    types = ()

    def __init__(self, *args, **kwargs):
        # TODO add `astype=None` option
        super().__init__(*self.types, **kwargs)
        self.iterable = Iterable(*args)

    def __call__(self, name, value):
        passed, value = super().__call__(name, value)
        if not passed:
            return False, value

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
    Check if argument is a homogenous ``set``.
    """
    types = (set,)

    def __init__(self, *args, **kwargs):
        # Sets should only be compared to other sets, hence: other_type=set
        super().__init__(*args, other_type=set, **kwargs)
