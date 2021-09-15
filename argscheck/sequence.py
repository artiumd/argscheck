from .core import Typed
from .numeric import Sized


class Sequence(Sized, Typed):
    """
    Check if argument is a homogeneous sequence, i.e. each item in the sequence satisfies the same set of checkers.

    A sequence is assumed to have the following properties:

    1. Has ``__len__()`` implemented.
    2. Has ``__getitem__()`` implemented, which accepts integers starting from zero and up to (and not including) the
       object's own length.
    3. Can be instantiated from an iterable.
    """
    types = (object,)

    def __init__(self, *args, **kwargs):
        # TODO add `astype=None` option
        super().__init__(*self.types, **kwargs)

        if args:
            self.item_checker = self._validate_args(args)
        else:
            self.item_checker = None

    def _get_items(self, name, value):
        items = []
        modified = False

        for i in range(len(value)):
            try:
                pre_check_item = value[i]
            except Exception:
                return False, TypeError(f'Failed when getting {name}[{i}], make sure {name} is a sequence.'), None

            passed, post_check_item = self.item_checker(f'{name}[{i}]', pre_check_item)
            if not passed:
                return False, post_check_item, None

            if post_check_item is not pre_check_item:
                modified = True

            items.append(post_check_item)

        return True, items, modified

    def _set_items(self, name, value, items):
        # Otherwise, create a new sequence of the same type, with the modified items
        try:
            return True, type(value)(items)
        except Exception:
            return False, TypeError(f'Failed on {type(value).__qualname__}(), make sure this type can be instantiated '
                                    f'from an iterable.')

    def __call__(self, name, value):
        passed, value = super().__call__(name, value)
        if not passed:
            return False, value

        # If Sequence was constructed with an empty *args, no need to iterate over items in the sequence
        if self.item_checker is None:
            return True, value

        # Get all items in the sequence, check (and possibly convert) each one, arrange them in a list
        passed, items, modified = self._get_items(name, value)
        if not passed:
            return False, items

        # Prepare return value, for an immutable sequence, a new sequence instance is created and returned, for a
        # mutable sequence, items are set inplace and the original sequence is returned.
        if modified:
            passed, value = self._set_items(name, value, items)
            if not passed:
                return False, value

        # TODO astype goes here

        return True, value


class Tuple(Sequence):
    """
    Same as :class:`.Sequence`, and argument must be a ``tuple`` instance.
    """
    types = (tuple,)


class NonEmptyTuple(Tuple):
    """
    Same as :class:`.Tuple`, and argument's length must be greater than zero.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, len_gt=0, **kwargs)


class MutableSequence(Sequence):
    """
    Check if argument is a homogeneous mutable sequence, i.e. each item in the sequence satisfies the same set of
    checkers.

    A mutable sequence is assumed to have the following properties:

    1. Has ``__len__()`` implemented.
    2. Has ``__getitem__()`` implemented, which accepts integers starting from zero and up to (and not including) the
       object's own length.
    3. Has ``__setitem__()`` implemented, which accepts the same keys as ``__getitem__()``.
    """
    def _set_items(self, name, value, items):
        for i, item in enumerate(items):
            try:
                value[i] = item
            except Exception as e:
                return False, TypeError(f'The following exception was raised while setting {name}[{i}]:\n{e}\n'
                                        f'Make sure {name} is a mutable sequence.')

        return True, value


class List(MutableSequence):
    """
    Same as :class:`.MutableSequence`, and argument must be a ``list`` instance.
    """
    types = (list,)


class NonEmptyList(List):
    """
    Same as :class:`.List`, and argument's length must be greater than zero.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, len_gt=0, **kwargs)
