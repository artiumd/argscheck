from .core import Typed
from .numeric import Sized
from . import Comparable
from .iter import Iterable


class Collection(Sized, Typed):
    """
    A collection is assumed to have the following properties:

    1. Has __len__ implemented.
    2. Is iterable.
    3. Can be instantiated from an iterable.
    """
    types = ()

    def __init__(self, *checker_likes, **kwargs):
        # TODO add `astype=None` option
        super().__init__(*self.types, **kwargs)
        self.iterable = Iterable(*checker_likes)

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
    types = (set,)

    def __init__(self, *args, **kwargs):
        # Sets should only be compared to other sets, hence: other_type=set
        super().__init__(*args, other_type=set, **kwargs)
