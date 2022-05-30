"""
Iterator and Iterable
=====================

This module contains checkers for iterator and iterable arguments.

In this context, an iterator is a class that has ``__next__()`` implemented, so each call to ``next()`` produces an
item, until finally ``StopIteration`` is raised.

An iterable is a class that has ``__iter__()`` implemented, so it can be iterated over by a for loop or by explicitly
creating an iterator with ``iter()`` and repeatedly calling ``next()`` on the resulting iterator.
"""
from .core import Checker


class Iterator(Checker, deferred=True):
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

        self.item_checker = Checker.from_checker_likes(args)
        self.name = self.i = self.iterator = None

    def __next__(self):
        name = self.name.format(self.i)
        self.i += 1

        # Get next item from iterator
        try:
            value = next(self.iterator)
        except TypeError:
            raise TypeError(f'Failed calling next() on {self.iterator!r}, make sure this object is an iterator.')
        except StopIteration as stop:
            # This clause is purely for readability
            raise stop

        # Check next item from iterator
        passed, value = self.item_checker._check(name, value)
        if not passed:
            raise value

        return value

    def _check(self, name, value):
        if not name:
            name = repr(self).lower()

        self.name = 'item {} from ' + name
        self.iterator = value
        self.i = 0

        return self


class Iterable(Iterator, deferred=True):
    """
    Same as :class:`.Iterator`, plus, ``x`` can be a plain iterable (not necessarily an iterator).

    :Example:

    .. code-block:: python

        from argscheck import Iterable

        # Each item must be an str or bool instance
        checker = Iterable(str, bool)

        # Can be iterated over with a for loop
        for item in checker.check(['a', True, 1.1]):
            print(item)     # prints "a\\n", "True\\n", then raises TypeError (1.1 is not an str or bool).

        # Can be iterated over manually
        iterator = iter(checker.check(['a', True, 1.1]))
        next(iterator)  # Passes, returns 'a'
        next(iterator)  # Passes, returns True
        next(iterator)  # Fails, raises TypeError (1.1 is not an str or bool).

    """
    def __iter__(self):
        # Create iterator from iterable
        try:
            self.iterator = iter(self.iterator)
        except TypeError:
            raise TypeError(f'Failed calling iter() on {self.iterator!r}, make sure this object is iterable.')

        self.i = 0

        return self
