import operator
from functools import partial

from .core import Checker, Typed


class Ordered(Checker):
    orders = dict(lt=dict(order_fn=operator.lt, order_name='less than'),
                  le=dict(order_fn=operator.le, order_name='less than or equal to'),
                  ne=dict(order_fn=operator.ne, order_name='not equal to'),
                  eq=dict(order_fn=operator.eq, order_name='equal to'),
                  ge=dict(order_fn=operator.ge, order_name='greater than or equal to'),
                  gt=dict(order_fn=operator.gt, order_name='greater than'))

    def __init__(self, *args, lt=None, le=None, ne=None, eq=None, ge=None, gt=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Arrange arguments in a dictionary for convenience
        order_args = dict(lt=lt, le=le, ne=ne, eq=eq, ge=ge, gt=gt)

        # Check that arguments are numbers or None
        for name, value in order_args.items():
            if value is not None and not isinstance(value, (int, float)):
                raise TypeError(f'Argument {name}={value!r} of {self!r}() must be a number or None.')

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
        self.checker_fns = [partial(self._check_order, other=value, **self.orders[name])
                            for name, value
                            in order_args.items()
                            if value is not None]

    @staticmethod
    def _get_not_none(x, y):
        if x is not None:
            return x
        if y is not None:
            return y

        return None

    @classmethod
    def _check_order(cls, name, value, other, order_fn, order_name):
        # Compare value, if comparison fails, return the caught exception
        try:
            if order_fn(value, other):
                return True, value
            else:
                return False, ValueError(f'Argument {name}={value!r} is expected to be {order_name} {other!r}.')
        except Exception as e:
            return False, e

    def __call__(self, name, value):
        passed, value = super().__call__(name, value)
        if not passed:
            return False, value

        for checker_fn in self.checker_fns:
            passed, value = checker_fn(name, value)
            if not passed:
                return False, value

        return True, value


class Sized(Checker):
    def __init__(self, *args, len_lt=None, len_le=None, len_ne=None, len_eq=None, len_ge=None, len_gt=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.len_checker = Int(lt=len_lt, le=len_le, ne=len_ne, eq=len_eq, ge=len_ge, gt=len_gt)

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


class Int(Ordered, Typed):
    def __init__(self, **kwargs):
        super().__init__(int, **kwargs)


class Float(Ordered, Typed):
    def __init__(self, **kwargs):
        super().__init__(float, **kwargs)


class Number(Ordered, Typed):
    def __init__(self, **kwargs):
        super().__init__(int, float, **kwargs)
