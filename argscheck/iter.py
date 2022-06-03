"""
Iterator and Iterable
=====================

This module contains checkers for iterator and iterable arguments.

In this context, an iterator is a class that has ``__next__()`` implemented, so each call to ``next()`` produces an
item, until finally ``StopIteration`` is raised.

An iterable is a class that has ``__iter__()`` implemented, so it can be iterated over by a for loop or by explicitly
creating an iterator with ``iter()`` and repeatedly calling ``next()`` on the resulting iterator.
"""
from .core import check, Checker, Wrapper


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
        self.item_checker = Checker.from_checker_likes(args)

    def check(self, name, value):
        if not name:
            name = repr(self).lower()

        return _IteratorWrapper(self.item_checker, value, 'item {} from ' + name)


class Iterable(Checker):
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
    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self.item_checker = Checker.from_checker_likes(args)

    def check(self, name, value):
        if not name:
            name = repr(self).lower()

        return _IterableWrapper(self.item_checker, value, 'item {} from ' + name)


class _IteratorWrapper(Wrapper):
    def __init__(self, checker, wrapped, name):
        self.checker = checker
        self.wrapped = wrapped
        self.name = name
        self.i = 0

    def __next__(self):
        # Update item name and counter
        name = self.name.format(self.i)
        self.i += 1

        # Get next item from iterator
        try:
            value = next(self.wrapped)
        except TypeError:
            raise TypeError(f'Failed calling next() on {self.iterator!r}, make sure this object is an iterator.')
        except StopIteration as stop:
            # This clause is purely for readability
            raise stop

        # Check next item from iterator
        return check(self.checker, value, name)


class _IterableWrapper(Wrapper):
    def __init__(self, checker, wrapped, name):
        self.checker = checker
        self.wrapped = wrapped
        self.name = name

    def __iter__(self):
        # Create iterator from iterable
        try:
            iterator = iter(self.wrapped)
        except TypeError:
            raise TypeError(f'Failed calling iter() on {self.wrapped!r}, make sure this object is iterable.')

        return _IteratorWrapper(self.checker, iterator, self.name)
