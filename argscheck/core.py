from functools import partial
import operator


class Checker:
    def __repr__(self):
        return type(self).__qualname__

    def __call__(self, name, value):
        return True, value

    def check(self, *args, **kwargs):
        # Make sure method is called properly and unpack argument's name and value
        if len(args) + len(kwargs) != 1:
            raise TypeError(f'{self!r}.check() must be called with a single positional or keyword argument.'
                            f' Got {len(args)} positional arguments and {len(kwargs)} keyword arguments.')
        if args:
            name, value = 'argument', args[0]
        if kwargs:
            name, value = next(iter(kwargs.items()))

        # Perform argument checking. If passed, return (possibly converted) value, otherwise, raise the returned
        # exception.
        passed, value_or_excp = self(name, value)
        if passed:
            return value_or_excp
        else:
            raise value_or_excp


def _validate_checker_like(name, value):
    if isinstance(value, tuple) and len(value) == 1:
        return _validate_checker_like(name, value[0])
    if isinstance(value, tuple) and len(value) > 1:
        return One(*value)
    if isinstance(value, Checker):
        return value
    if isinstance(value, type) and issubclass(value, Checker):
        return value()
    if isinstance(value, type):
        return Typed(value)

    raise TypeError(f'Argument {name}={value!r} is expected to be a checker-like.')


class Typed(Checker):
    def __init__(self, typ, **kwargs):
        super().__init__(**kwargs)

        if not isinstance(typ, type):
            raise TypeError(f'Argument typ={type!r} of {self!r}() is expected to be a type.')

        self.typ = typ

    def __call__(self, name, value):
        passed, value = super().__call__(name, value)
        if not passed:
            return False, value

        if isinstance(value, self.typ):
            return True, value
        else:
            return False, TypeError(f'Argument {name}={value!r} is expected to be of type {self.typ!r}.')


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

    @staticmethod
    def _check_order(name, value, other, order_fn, order_name):
        # Compare value, if comparison fails, return the caught exception
        try:
            res = order_fn(value, other)
        except Exception as e:
            return False, e

        if res:
            return True, value
        else:
            return False, ValueError(f'Argument {name}={value!r} is expected to be {order_name} {other!r}.')

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


class One(Checker):
    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)

        if len(args) < 2:
            raise TypeError(f'{self!r}() must be called with at least two positional arguments, got {args!r}.')

        # Validate checker-like positional arguments
        self.checkers = [_validate_checker_like(f'args[{i}]', arg)
                         for i, arg
                         in enumerate(args)]

    def __call__(self, name, value):
        passed, value = super().__call__(name, value)
        if not passed:
            return False, value

        passed_count = 0
        ret_value = None

        # Apply all checkers to value, make sure only one passes
        for checker in self.checkers:
            passed, ret_value_ = checker(name, value)
            if passed:
                passed_count += 1
                ret_value = ret_value_

        # The `One` checker passes only if exactly one of its checkers passes
        if passed_count == 1:
            return True, ret_value
        else:
            checkers = ', '.join([repr(checker) for checker in self.checkers])
            return False, ValueError(f'Argument {name}={value!r} is expected to pass exactly one of: {checkers}.')


class Sequence(Sized, Typed):
    def __init__(self, *args, **kwargs):
        super().__init__(list, tuple, **kwargs)

        self.item_checker = _validate_checker_like('args', args)

    def __call__(self, name, value):
        passed, value = super().__call__(name, value)
        if not passed:
            return False, value

        items = []
        for i, item in enumerate(value):
            passed, item = self.item_checker(f'{name}[{i}]', item)
            if not passed:
                return False, item

            items.append(item)

        value = type(value)(items)

        return True, value


class String(Typed):
    def __init__(self, **kwargs):
        super().__init__(str, **kwargs)


class Int(Ordered, Typed):
    def __init__(self, **kwargs):
        super().__init__(int, **kwargs)


class Number(Ordered, Typed):
    def __init__(self, **kwargs):
        super().__init__(int, float, **kwargs)
