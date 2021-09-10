from .core import Checker, Typed, Comparable


_ints = (int,)
_floats = (float,)
_numbers = _ints + _floats


class Sized(Checker):
    def __init__(self, *args, len_lt=None, len_le=None, len_ne=None, len_eq=None, len_ge=None, len_gt=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Length must be an int and must only be compared to an int
        self.len_checker = Int(lt=len_lt, le=len_le, ne=len_ne, eq=len_eq, ge=len_ge, gt=len_gt, other_type=_ints)

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


class Int(Comparable, Typed):
    def __init__(self, other_type=_numbers, **kwargs):
        super().__init__(*_ints, other_type=other_type, **kwargs)


class Float(Comparable, Typed):
    def __init__(self, other_type=_numbers, **kwargs):
        super().__init__(*_floats, other_type=other_type, **kwargs)


class Number(Comparable, Typed):
    def __init__(self, other_type=_numbers, **kwargs):
        super().__init__(*_numbers, other_type=other_type, **kwargs)


"""
Positive
"""


class PositiveNumber(Number):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, gt=0, **kwargs)


class PositiveInt(Int):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, gt=0, **kwargs)


class PositiveFloat(Float):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, gt=0, **kwargs)


"""
Non Negative
"""


class NonNegativeNumber(Number):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, ge=0, **kwargs)


class NonNegativeInt(Int):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, ge=0, **kwargs)


class NonNegativeFloat(Float):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, ge=0, **kwargs)


"""
Negative
"""


class NegativeNumber(Number):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, lt=0, **kwargs)


class NegativeInt(Int):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, lt=0, **kwargs)


class NegativeFloat(Float):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, lt=0, **kwargs)


"""
Non Positive
"""


class NonPositiveNumber(Number):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, le=0, **kwargs)


class NonPositiveInt(Int):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, le=0, **kwargs)


class NonPositiveFloat(Float):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, le=0, **kwargs)


# Aliases
Integer = Int
Num = Number

PositiveInteger = PosInt = PositiveInt
PosNumber = PosNum = PositiveNumber
PosFloat = PositiveFloat

NonNegativeInteger = NonNegInt = NonNegativeInt
NonNegNumber = NonNegNum = NonNegativeNumber
NonNegFloat = NonNegativeFloat


NegativeInteger = NegInt = NegativeInt
NegNumber = NegNum = NegativeNumber
NegFloat = NegativeFloat


NonPositiveInteger = NonPosInt = NonPositiveInt
NonPosNumber = NonPosNum = NonPositiveNumber
NonPosFloat = NonPositiveFloat
