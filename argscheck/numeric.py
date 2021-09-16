"""
Numeric
=======
"""
from .core import Checker, Typed, Comparable, Optional


_ints = (int,)
_floats = (float,)
_numbers = _ints + _floats


class Number(Comparable, Typed):
    """
    Check if argument is of a numeric type (``int`` or ``float``) and optionally, compares it to other value(s) using
    any of the following binary operators: ``{< | <= | != | == | >= | >}``.

    :param other_type: *Optional[Union[Type, Tuple[Type]]]* – restricts the types to which the argument can
       be compared, e.g. ``other_type=int`` with ``ne=1.0`` will raise a ``TypeError``. By default, argument can only be
       compared to other ``int`` or ``float`` objects.
    """
    def __init__(self, other_type=_numbers, **kwargs):
        super().__init__(*_numbers, other_type=other_type, **kwargs)


class Int(Comparable, Typed):
    """
    Same as :class:`.Number`, plus, argument must be an ``int``.
    """
    def __init__(self, other_type=_numbers, **kwargs):
        super().__init__(*_ints, other_type=other_type, **kwargs)


class Float(Comparable, Typed):
    """
    Same as :class:`.Number`, plus, argument must be a ``float``.
    """
    def __init__(self, other_type=_numbers, **kwargs):
        super().__init__(*_floats, other_type=other_type, **kwargs)


"""
Positive
"""


class PositiveNumber(Number):
    """
    Same as :class:`.Number`, plus, ``x > 0`` must be ``True``.

    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, gt=0, **kwargs)


class PositiveInt(Int):
    """
    Same as :class:`.Int`, plus, ``x > 0`` must be ``True``.

    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, gt=0, **kwargs)


class PositiveFloat(Float):
    """
    Same as :class:`.Float`, plus, ``x > 0`` must be ``True``.

    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, gt=0, **kwargs)


"""
Non Negative
"""


class NonNegativeNumber(Number):
    """
    Same as :class:`.Number`, plus, ``x >= 0`` must be ``True``.

    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, ge=0, **kwargs)


class NonNegativeInt(Int):
    """
    Same as :class:`.Int`, plus, ``x >= 0`` must be ``True``.

    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, ge=0, **kwargs)


class NonNegativeFloat(Float):
    """
    Same as :class:`.Float`, plus, ``x >= 0`` must be ``True``.

    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, ge=0, **kwargs)


"""
Negative
"""


class NegativeNumber(Number):
    """
    Same as :class:`.Number`, plus, ``x < 0`` must be ``True``.

    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, lt=0, **kwargs)


class NegativeInt(Int):
    """
    Same as :class:`.Int`, plus, ``x < 0`` must be ``True``.

    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, lt=0, **kwargs)


class NegativeFloat(Float):
    """
    Same as :class:`.Float`, plus, ``x < 0`` must be ``True``.

    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, lt=0, **kwargs)


"""
Non Positive
"""


class NonPositiveNumber(Number):
    """
    Same as :class:`.Number`, plus, ``x <= 0`` must be ``True``.

    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, le=0, **kwargs)


class NonPositiveInt(Int):
    """
    Same as :class:`.Int`, plus, ``x <= 0`` must be ``True``.

    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, le=0, **kwargs)


class NonPositiveFloat(Float):
    """
    Same as :class:`.Float`, plus, ``x <= 0`` must be ``True``.

    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, le=0, **kwargs)


_optional_non_neg = Optional(NonNegativeInt)


class Sized(Checker):
    """
    Check argument's length (as returned from calling ``len()`` on it).

    :param len_lt: *Optional[int]* – Check if ``len(x) < len_lt``.
    :param len_le: *Optional[int]* – Check if ``len(x) <= len_le``.
    :param len_ne: *Optional[int]* – Check if ``len(x) != len_ne``.
    :param len_eq: *Optional[int]* – Check if ``len(x) == len_eq``.
    :param len_ge: *Optional[int]* – Check if ``len(x) >= len_ge``.
    :param len_gt: *Optional[int]* – Check if ``len(x) > len_gt``.

    :Example:

    .. code-block:: python

        from argscheck import Sized

        # Check if length is equal to 3
        checker = Sized(len_eq=3)

        checker.check(['a', 'b', 'c'])  # Passes, returns ['a', 'b', 'c']
        checker.check('abc')            # Passes, returns 'abc'
        checker.check({'a', 'b'})       # Fails, raises ValueError (length is 2 instead of 3)
        checker.check(123)              # Fails, raises TypeError (int does not have a length)

    """
    def __init__(self, *args, len_lt=None, len_le=None, len_ne=None, len_eq=None, len_ge=None, len_gt=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Length must be an int and must only be compared to an int
        self.len_checker = Int(lt=len_lt, le=len_le, ne=len_ne, eq=len_eq, ge=len_ge, gt=len_gt, other_type=_ints)

        # Check that no negative values were provided
        _optional_non_neg.check(len_lt=len_lt)
        _optional_non_neg.check(len_le=len_le)
        _optional_non_neg.check(len_ne=len_ne)
        _optional_non_neg.check(len_eq=len_eq)
        _optional_non_neg.check(len_ge=len_ge)
        _optional_non_neg.check(len_gt=len_gt)

    def __call__(self, name, value):
        passed, value = super().__call__(name, value)
        if not passed:
            return False, value

        # Get value's length, if it fails, return the caught exception
        try:
            len_value = len(value)
        except Exception as e:
            return False, e

        # Check length
        passed, e = self.len_checker(f'length of {name}', len_value)
        if not passed:
            return False, e

        return True, value


class NonEmpty(Sized):
    """
    Check if argument's length is greater than zero.

    :Example:

    .. code-block:: python

        from argscheck import NonEmpty

        # Check if non empty
        checker = NonEmpty()

        checker.check(['a', 'b', 'c'])  # Passes, returns ['a', 'b', 'c']
        checker.check('abc')            # Passes, returns 'abc'
        checker.check('')               # Fails, raises ValueError (empty string)
        checker.check([])               # Fails, raises ValueError (empty list)
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, len_lt=None, len_le=None, len_ne=None, len_eq=None, len_ge=None, len_gt=0, **kwargs)
