import operator
from functools import partial

from .core import Checker, Typed


class Comparable(Checker):
    comparisons = dict(lt=dict(comp_fn=operator.lt, comp_name='less than'),
                       le=dict(comp_fn=operator.le, comp_name='less than or equal to'),
                       ne=dict(comp_fn=operator.ne, comp_name='not equal to'),
                       eq=dict(comp_fn=operator.eq, comp_name='equal to'),
                       ge=dict(comp_fn=operator.ge, comp_name='greater than or equal to'),
                       gt=dict(comp_fn=operator.gt, comp_name='greater than'))

    def __init__(self, *args, lt=None, le=None, ne=None, eq=None, ge=None, gt=None, other_type=object, **kwargs):
        super().__init__(*args, **kwargs)

        # Arrange arguments in a dictionary for convenience
        others = dict(lt=lt, le=le, ne=ne, eq=eq, ge=ge, gt=gt)

        # Check that arguments are numbers or None
        for name, value in others.items():
            if value is not None and not isinstance(value, other_type):
                raise TypeError(f'Argument {name}={value!r} of {self!r}() must be {other_type!r} or None.')

        if (lt is not None) and (le is not None):
            raise TypeError(f'Arguments lt={lt!r} and le={le!r} of {self!r}() must not be both provided.')

        if (ne is not None) and (eq is not None):
            raise TypeError(f'Arguments ne={ne!r} and eq={eq!r} of {self!r}() must not be both provided.')

        if (ge is not None) and (gt is not None):
            raise TypeError(f'Arguments ge={ge!r} and gt={gt!r} of {self!r}() must not be both provided.')

        if (eq is not None) and any(p is not None for p in {lt, le, ne, ge, gt}):
            raise TypeError(f'Argument eq={eq!r} excludes all other arguments of {self!r}.')

        # Check that lower bound is indeed lower than upper bound (if both are provided)
        lb = self._get_not_none(ge, gt)
        ub = self._get_not_none(le, lt)
        if (lb is not None) and (ub is not None) and (lb > ub):
            raise ValueError(f'Lower bound {lb!r} of {self!r} must be lower than the upper bound {ub!r}.')

        # Create order checker functions for the arguments that are not None
        self.comparators = [partial(self._compare, other=other, **self.comparisons[name])
                            for name, other
                            in others.items()
                            if other is not None]

    @staticmethod
    def _get_not_none(x, y):
        if x is not None:
            return x
        if y is not None:
            return y

        return None

    @classmethod
    def _compare(cls, name, value, other, comp_fn, comp_name):
        # Compare value, if comparison fails, return the caught exception
        try:
            ret = comp_fn(value, other)
        except Exception as e:
            # TODO add verbose message
            return False, e

        if ret:
            return True, value
        else:
            return False, ValueError(f'Argument {name}={value!r} is expected to be {comp_name} {other!r}.')

    def __call__(self, name, value):
        passed, value = super().__call__(name, value)
        if not passed:
            return False, value

        for comparator in self.comparators:
            passed, value = comparator(name, value)
            if not passed:
                return False, value

        return True, value


class Sized(Checker):
    def __init__(self, *args, len_lt=None, len_le=None, len_ne=None, len_eq=None, len_ge=None, len_gt=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.len_checker = Int(lt=len_lt, le=len_le, ne=len_ne, eq=len_eq, ge=len_ge, gt=len_gt, other_type=int)

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
        passed, e = self.len_checker(f'len({name})', len_value)
        if not passed:
            return False, e

        return True, value


class Int(Comparable, Typed):
    def __init__(self, other_type=(int, float), **kwargs):
        super().__init__(int, other_type=other_type, **kwargs)


class Float(Comparable, Typed):
    def __init__(self, other_type=(int, float), **kwargs):
        super().__init__(float, other_type=other_type, **kwargs)


class Number(Comparable, Typed):
    def __init__(self, other_type=(int, float), **kwargs):
        super().__init__(int, float, other_type=other_type, **kwargs)
