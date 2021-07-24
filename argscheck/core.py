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
            raise TypeError(f'{self!r}.check() must be called with a single positional argument or a single keyword.'
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


class CheckerLike(Checker):
    def __call__(self, name, value):
        passed, value = super().__call__(name, value)
        if not passed:
            return False, value

        if isinstance(value, tuple) and len(value) == 1:
            return self(name, value[0])
        if isinstance(value, tuple):
            raise NotImplementedError()
        if isinstance(value, Checker):
            return True, value
        if isinstance(value, type) and issubclass(value, Checker):
            return True, value()
        if isinstance(value, type):
            return True, Typed(value)
        # if isinstance(value, tuple) and all(isinstance(item, type) for item in value):
        #     return True, Typed(*value)

        return False, TypeError(f'Argument {name}={value!r} is expected to be a checker-like.')


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

        if lt is not None and le is not None:
            raise ValueError(f'Arguments lt={lt!r} and le={le!r} of {self!r}() must not be both provided.')

        if ne is not None and eq is not None:
            raise ValueError(f'Arguments ne={ne!r} and eq={eq!r} of {self!r}() must not be both provided.')

        if ge is not None and gt is not None:
            raise ValueError(f'Arguments ge={ge!r} and gt={gt!r} of {self!r}() must not be both provided.')

        if eq is not None and any(p is not None for p in {lt, le, ne, ge, gt}):
            raise ValueError(f'Argument eq={eq!r} excludes all other arguments of {self!r}.')

        # Arrange arguments in dictionary for easy access
        order_args = dict(lt=lt, le=le, ne=ne, eq=eq, ge=ge, gt=gt)

        # Check that arguments are numbers or None
        for name, value in order_args.items():
            if value is not None and not isinstance(value, (int, float)):
                raise TypeError(f'Argument {name}={value!r} of {self!r}() must be a number or None.')

        # Create order checker functions for the arguments that are not None
        self.checker_fns = [partial(self._check_order, other=value, **self.orders[name])
                            for name, value
                            in order_args.items()
                            if value is not None]

    @staticmethod
    def _check_order(name, value, other, order_fn, order_name):
        if order_fn(value, other):
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

        # Try and get the length of value, if fails, return the raised exception
        try:
            len_value = len(value)
        except Exception as e:
            return False, e

        passed, len_value = self.len_checker(f'len({name})', len_value)
        if not passed:
            return False, len_value

        return True, value


class Sequence(Sized, Typed):
    def __init__(self, *args, **kwargs):
        super().__init__(list, tuple, **kwargs)
        passed, value = CheckerLike()('args', args)
        if not passed:
            raise value

        self.item_checker = value

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
        super().__init__(float, **kwargs)


if __name__ == '__main__':
    a = Typed(int).check(a=1)
    print(a)

    a = CheckerLike().check(a=str)
    print(a)

    a = String().check(a='1')
    print(a)

    a = Number(ne=23).check(a=2.0)
    print(a)

    a = CheckerLike().check(a=int)
    print(a)

    a = CheckerLike().check(a=String)
    print(a)

    a = CheckerLike().check(a=String())
    print(a)

    a = Sized(len_ge=4).check(a=4*[1])
    print(a)

    a = Sequence(String).check(a=(['2']))
    print(a)