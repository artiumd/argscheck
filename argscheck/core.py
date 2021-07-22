from functools import partial
import operator


class Checker:
    def __repr__(self):
        return type(self).__qualname__

    def check_(self, name, value):
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

        # Perform argument checking, if passed, apply conversion, otherwise raise the error returned
        passed, value_or_ex = self.check_(name, value)
        if passed:
            return value_or_ex
        else:
            raise value_or_ex


class CheckerLike(Checker):
    def check_(self, name, value):
        passed, value = super().check_(name, value)
        if not passed:
            return False, value

        if isinstance(value, Checker):
            return True, value
        if issubclass(value, Checker):
            return True, value()
        if _is_type_or_tuple_of_types(value):
            return True, Typed(value)

        return False, TypeError(f'Argument {name}={value!r} is expected to be a checker-like.')


class Typed(Checker):
    def __init__(self, typ, **kwargs):
        super().__init__(**kwargs)

        if isinstance(typ, type):
            typ = (typ,)

        if not _is_type_or_tuple_of_types(typ):
            raise TypeError(f'Argument typ={typ!r} of {self!r}() is expected to be a type or a non-empty tuple of types.')

        self.typ = typ

    def check_(self, name, value):
        passed, value = super().check_(name, value)
        if not passed:
            return False, value

        if isinstance(value, self.typ):
            return True, value
        else:
            return False, TypeError(f'Argument {name}={value!r} is expected to be of type {self.typ!r}.')


def _check_order(name, value, other, order_fn, order_name):
    if order_fn(value, other):
        return True, value
    else:
        return False, ValueError(f'Argument {name}={value!r} is expected to be {order_name} {other!r}.')


def _is_type_or_tuple_of_types(typ):
    if not isinstance(typ, tuple):
        typ = (typ,)

    return typ and all(isinstance(item, type) for item in typ)


class Ordered(Checker):
    orders = dict(lt=dict(order_fn=operator.lt, order_name='less than'),
                  le=dict(order_fn=operator.le, order_name='less than or equal to'),
                  ne=dict(order_fn=operator.ne, order_name='not equal to'),
                  eq=dict(order_fn=operator.eq, order_name='equal to'),
                  ge=dict(order_fn=operator.ge, order_name='greater than or equal to'),
                  gt=dict(order_fn=operator.gt, order_name='greater than'))

    def __init__(self, lt=None, le=None, ne=None, eq=None, ge=None, gt=None, **kwargs):
        super().__init__(**kwargs)

        if lt is not None and le is not None:
            raise ValueError(f'Arguments lt={lt!r} and le={le!r} of {self!r}() must not be both provided.')

        if ne is not None and eq is not None:
            raise ValueError(f'Arguments ne={ne!r} and eq={eq!r} of {self!r}() must not be both provided.')

        if ge is not None and gt is not None:
            raise ValueError(f'Arguments ge={ge!r} and gt={gt!r} of {self!r}() must not be both provided.')

        if eq is not None and any(p is not None for p in {lt, le, ne, ge, gt}):
            raise ValueError(f'Argument eq={eq!r} excludes all other arguments of {self!r}.')

        # Create order checker functions for the arguments that are not None
        self.checker_fns = [partial(_check_order, other=value, **self.orders[name])
                            for name, value
                            in dict(lt=lt, le=le, ne=ne, eq=eq, ge=ge, gt=gt).items()
                            if value is not None]

    def check_(self, name, value):
        passed, value = super().check_(name, value)
        if not passed:
            return False, value

        for checker_fn in self.checker_fns:
            passed, value = checker_fn(name, value)
            if not passed:
                return False, value

        return True, value


class String(Typed):
    def __init__(self, **kwargs):
        super().__init__(typ=str, **kwargs)


class Number(Ordered, Typed):
    def __init__(self, **kwargs):
        super().__init__(typ=(int, float), **kwargs)


if __name__ == '__main__':
    a = Typed(int).check(a=1)
    print(a)

    a = CheckerLike().check(a=str)
    print(a)

    a = String().check(a='1')
    print(a)

    a = Int(ne=2).check(a=2.0)
    print(a)
