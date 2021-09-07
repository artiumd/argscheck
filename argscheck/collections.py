from .core import Typed
from .numeric import Sized
from .iter import Iterable


class Collection(Sized, Typed):
    types = ()

    def __init__(self, *checker_likes, **kwargs):
        super().__init__(*self.types, **kwargs)
        self.iterable = Iterable(*checker_likes)

    def __call__(self, name, value):
        passed, value = super().__call__(name, value)
        if not passed:
            return False, value

        type_ = type(value)

        try:
            value = type_(self.iterable(name, value))
        except Exception as e:
            return False, e

        return True, value


class Tuple(Collection):
    types = (tuple,)


class List(Collection):
    types = (list,)


class Set(Collection):
    types = (set,)
