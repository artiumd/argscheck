"""
Iterator and Iterable
=====================

This page documents checkers for iterators and iterable objects.

We define and iterator as a class that:

1. Has `__next__()` implemented.
2. Each call to `next()` on iterator instances returns some value, until finally `StopIteration` is raised.

We define an iterable as a class that:

1. Has `__iter__()` implemented.
2. Calling `iter()` on iterable instances returns an iterator.

Iterators and iterables can be homogeneous, i.e. all items they yield satisfy the same set of conditions.

Homogeneity can be checked for by providing one or more positional arguments to the checker's constructor.

The usage of the `Iterator` and `Iterable` checkers, does not follow the usual pattern of:

.. code-block:: python

    checker = SomeChecker()
    check(checker, good_value)  # Passes, the good value is returned
    check(checker, bad_value)  # Fails, an exception is raised

Instead, calling `check()` returns a wrapper around the (iterator or iterable) value, and checking is preformed as the
values are being produced by the iterator or iterable.

See examples for :class:`.Iterator` and :class:`.Iterable`.

.. warning::

       Composing :class:`.Iterator`, :class:`.Iterable` inside other checkers has limited support (only
       :class:`~argscheck.optional.Optional` is supported).

       e.g. ``Collection(Iterable(int))`` is not supported (but ``Iterable(Collection(int))`` is supported).
"""

from .core import check, Checker, Wrapper, RAISE_ON_ERROR_DEFAULT


class Iterator(Checker):
    """
    Check if `x` is a (possible homogeneous) iterator.

    :param args: *Optional[Tuple[CheckerLike]]* –  If provided, apply the given check to each item from `x`.

    :Example:

    .. code-block:: python

        from argscheck import check, Iterator


        # Each item must be an str or bool instance
        iterator = check(Iterator(str, bool), iter(['a', True, 1.1]))

        next(iterator)  # Passes, 'a' is returned
        next(iterator)  # Passes, True is returned
        next(iterator)  # Fails, a TypeError is raised (1.1 is not an str or bool).

    """

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)

        if args:
            self.item_checker = Checker.from_checker_likes(args)
        else:
            self.item_checker = None

    def check(self, name, value, **kwargs):
        if not name:
            name = repr(self).lower()

        return _IteratorWrapper(self.item_checker, value, 'item {} from ' + name, **kwargs)


class Iterable(Checker):
    """
    Check if `x` is a (possible homogeneous) iterable.

    :param args: *Optional[Tuple[CheckerLike]]* –  If provided, apply the given check to each item from `x`.

    :Example:

    .. code-block:: python

        from argscheck import check, Iterable


        # Each item must be an str or bool instance
        for item in check(Iterable(str, bool), ['a', True, 1.1]):
            print(item)     # prints "a\\n", "True\\n", then raises TypeError (1.1 is not an str or bool).

    """
    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)

        if args:
            self.item_checker = Checker.from_checker_likes(args)
        else:
            self.item_checker = None

    def check(self, name, value, **kwargs):
        if not name:
            name = repr(self).lower()

        return _IterableWrapper(self.item_checker, value, 'item {} from ' + name, **kwargs)


class _IteratorWrapper(Wrapper):
    def __init__(self, checker, wrapped, name, raise_on_error=RAISE_ON_ERROR_DEFAULT):
        self.checker = checker
        self.wrapped = wrapped
        self.name = name
        self.raise_on_error = raise_on_error
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
        if self.checker is not None:
            return check(self.checker, value, name, self.raise_on_error)
        elif self.raise_on_error:
            return value
        else:
            return True, value, value


class _IterableWrapper(Wrapper):
    def __init__(self, checker, wrapped, name, raise_on_error=RAISE_ON_ERROR_DEFAULT):
        self.checker = checker
        self.wrapped = wrapped
        self.name = name
        self.raise_on_error = raise_on_error

    def __iter__(self):
        # Create iterator from iterable
        try:
            iterator = iter(self.wrapped)
        except TypeError:
            raise TypeError(f'Failed calling iter() on {self.wrapped!r}, make sure this object is iterable.')

        return _IteratorWrapper(self.checker, iterator, self.name, self.raise_on_error)
