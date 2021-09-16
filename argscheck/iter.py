"""
Iterator and Iterable
=====================
"""
from .core import Checker


class Iterator(Checker):
    """
    Check if ``x`` is a homogeneous iterator, i.e. each item satisfies the same set of checkers.

    The usage of the ``Iterator`` checker is a little different than the rest: calling ``check(x)`` returns a wrapper
    around ``x``, and calling ``next()`` on it will call ``next()`` on ``x`` and check each item before it is returned.

    :param args: *Tuple[CheckerLike]* – Describes what each item from the iterator must be.

    :Example:

    .. code-block:: python

        from argscheck import Iterator

        # Each item must be an str or bool instance
        checker = Iterator(str, bool)
        iterator = checker.check(iter(['a', True, 1.1]))

        next(iterator)  # Passes, returns 'a'
        next(iterator)  # Passes, returns True
        next(iterator)  # Fails, raises TypeError (1.1 is not an str or bool).

    """
    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)

        self.item_checker = self._validate_args(args)
        self.name = self.i = self.iterator = None

    def check(self, *args, **kwargs):
        name, value = self._resolve_name_value(*args, **kwargs)

        return self.__call__(name, value)

    def __call__(self, name, value):
        self.name = "{}'th item from " + str(name)
        self.iterator = value
        self.i = 0

        return self

    def __next__(self):
        name = self.name.format(self.i)
        self.i += 1
        value = next(self.iterator)
        passed, value = self.item_checker(name, value)

        if not passed:
            raise value

        return value


class Iterable(Iterator):
    """
    Same as :class:`.Iterator`, plus, ``x`` can be a plain iterable (not necessarily an iterator).

    :Example:

    .. code-block:: python

        from argscheck import Iterable

        # Each item must be an str or bool instance
        checker = Iterable(str, bool)
        iterable = checker.check(['a', True, 1.1])

        iterator = iter(iterable)
        next(iterator)  # Passes, returns 'a'
        next(iterator)  # Passes, returns True
        next(iterator)  # Fails, raises TypeError (1.1 is not an str or bool).

    """
    def __iter__(self):
        self.iterator = iter(self.iterator)

        return self
