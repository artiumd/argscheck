from .core import Sized, Typed
from .iter import Iterable


class Sequence(Sized, Typed):
    type_ = object

    def __init__(self, *checker_likes, **kwargs):
        super().__init__(self.type_, **kwargs)
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


class Tuple(Sequence):
    type_ = tuple


class List(Sequence):
    type_ = list


class Set(Sequence):
    type_ = set
