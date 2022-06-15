"""
Sequences
=========

This page documents checkers for sequence objects.

We define a sequence as a class that:

1. Implements `__len__()`.
2. Implements `__getitem__()`, which accepts (among others) integers starting from zero and up to (and not including)
    the object's own length.
3. Can be instantiated from an iterable.

We define a mutable sequence as a class that:

1. Is a sequence.
2. Implements `__setitem__()`, which accepts the same keys as `__getitem__()`.

Sequences (mutable or otherwise)  can be homogeneous, i.e. all items in it satisfy the same set of conditions.

Homogeneity can be checked for using by providing one or more positional arguments to the checker's constructor.

Checkers that convert values (like :class:`.Optional` for example) are applied as follows:

1. For mutable sequences, converted items are set inplace.
2. For (non-mutable) sequences, a new sequence instance is created from the converted items (this will happen only if
   actual conversion took place for at least one item).
"""

from .core import Checker, Typed, Wrapper
from .numeric import Sized, NonEmpty


class Sequence(Sized, Typed):
    """
    Check if `x` is a sequence.

    :Example:

    .. code-block:: python

        from argscheck import check, Sequence


        # Check if a set of length at least 2
        checker = Sequence(str, len_ge=2)

        check(checker, ['a', 'b'])  # Passes, ['a', 'b'] is returned
        check(checker, {'a', 'b'})  # Fails, a TypeError is raised (set is not a sequence)
        check(checker, ['a'])       # Fails, a ValueError is raised (length is less than 2)
        check(checker, ['a', 1])    # Fails, a TypeError is raised (not all items are str)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*self.types, **kwargs)

        if args:
            self.item_checker = Checker.from_checker_likes(args)
        else:
            self.item_checker = None

    def check(self, name, value, **kwargs):
        passed, value = super().check(name, value)
        if not passed:
            return False, value

        # If Sequence was constructed with an empty *args, no need to iterate over items in the sequence
        if self.item_checker is None:
            return True, value

        # Get all items in the sequence, check (and possibly convert) each one, arrange them in a list
        passed, items, modified = self._get_items(name, value)
        if not passed:
            return False, items

        # If none of the items were modified, can return now without setting them
        if not modified:
            return True, value

        # Prepare return value. For an immutable sequence, a new sequence instance is created and returned, for a
        # mutable sequence, items are set inplace and the original sequence is returned.
        passed, value = self._set_items(name, value, items)
        if not passed:
            return False, value

        return True, value

    def _get_items(self, name, value):
        items = []
        items_append = items.append
        modified = False

        item_name, seq_name = (name + '[{}]', name) if name else ('sequence item {}', 'it')

        # Get length
        try:
            length = len(value)
        except TypeError:
            err_msg = f'Failed calling len(), make sure {seq_name} is a sequence.'

            return False, TypeError(err_msg), None

        # Form a list of returned items by getting each item by its integer index, and applying the item checker on it
        for i in range(length):
            # Call __getitem__(), if call fails return TypeError (sequences must implement __getitem__())
            try:
                pre_check_item = value[i]
            except TypeError:
                e = TypeError(f'Failed getting {item_name.format(i)}, make sure {seq_name} is a sequence.')

                return False, e, None

            result = self.item_checker.check(item_name.format(i), pre_check_item)

            if isinstance(result, Wrapper):
                err_msg = f'{self!r} does not support nesting deferred checkers such as {self.item_checker!r}.'

                raise NotImplementedError(err_msg)

            passed, post_check_item = result
            if not passed:
                return False, post_check_item, None

            # If current item was modified by self.item_checker, set modified to True to signal .check() that at least
            # one item was modified and that all items need to be set back to the sequence
            if post_check_item is not pre_check_item:
                modified = True

            items_append(post_check_item)

        return True, items, modified

    def _set_items(self, name, value, items):
        # For non-mutable sequences, create a new sequence of the same type, with the modified items
        try:
            return True, type(value)(items)
        except TypeError:
            class_name = value.__class__.__name__
            err_msg = f'Failed on {class_name}(), make sure this type can be instantiated from an iterable.'

            return False, TypeError(err_msg)


class NonEmptySequence(NonEmpty, Sequence):
    """
    Same as :class:`.Sequence`, plus, the length of `x` must be greater than zero.

    :meta skip-extend-docstring:
    """
    pass


class Tuple(Sequence, types=(tuple,)):
    """
    Same as :class:`.Sequence`, plus, `x` must be a `tuple`.

    :meta skip-extend-docstring:
    """
    pass


class NonEmptyTuple(NonEmpty, Tuple):
    """
    Same as :class:`.Tuple`, plus, the length of `x` must be greater than zero.

    :meta skip-extend-docstring:
    """
    pass


class MutableSequence(Sequence):
    """
    Check if `x` is a mutable sequence.

    """
    def _set_items(self, name, value, items):
        item_name, seq_name = (name + '[{}]', name) if name else ('sequence item {}', 'it')

        # Iterate over checked items, set each one to the mutable sequence by its integer index
        for i, item in enumerate(items):
            try:
                value[i] = item
            except TypeError:
                err_msg = f'Failed setting {item_name.format(i)}, make sure {seq_name} is a mutable sequence.'

                return False, TypeError(err_msg)

        return True, value


class NonEmptyMutableSequence(NonEmpty, MutableSequence):
    """
    Same as :class:`.MutableSequence`, plus, the length of `x` must be greater than zero.

    :meta skip-extend-docstring:
    """
    pass


class List(MutableSequence, types=(list,)):
    """
    Same as :class:`.MutableSequence`, plus, `x` must be a `list`.

    :meta skip-extend-docstring:
    """
    pass


class NonEmptyList(NonEmpty, List):
    """
    Same as :class:`.List`, plus, the length of `x` must be greater than zero.

    :meta skip-extend-docstring:
    """
    pass
