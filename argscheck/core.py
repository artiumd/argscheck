import operator
from functools import partial


class Sentinel:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name


class Checker:
    def __repr__(self):
        return type(self).__qualname__

    def __call__(self, name, value):
        return True, value

    def _validate_args(self, value, name='args'):
        if isinstance(value, tuple) and len(value) == 1:
            return self._validate_args(value[0], name=f'{name}[0]')
        if isinstance(value, tuple) and len(value) > 1:
            return One(*value)
        if isinstance(value, Checker):
            return value
        if isinstance(value, type) and issubclass(value, Checker):
            return value()
        if isinstance(value, type):
            return Typed(value)

        raise TypeError(f'{self!r} expects that {name}={value!r} is a checker-like.')

    def _resolve_name_value(self, *args, **kwargs):
        # Make sure method is called properly and unpack argument's name and value
        if len(args) + len(kwargs) != 1:
            raise TypeError(f'{self!r}.check() must be called with a single positional or keyword argument.'
                            f' Got {len(args)} positional arguments and {len(kwargs)} keyword arguments.')
        if args:
            return '', args[0]
        else:
            return next(iter(kwargs.items()))

    def check(self, *args, **kwargs):
        name, value = self._resolve_name_value(*args, **kwargs)

        # Perform argument checking. If passed, return (possibly converted) value, otherwise, raise the returned
        # exception.
        passed, value_or_excp = self(name, value)
        if passed:
            return value_or_excp
        else:
            raise value_or_excp


class Typed(Checker):
    """
    Check if argument is an instance of a given type (or types).

    Internally, ``types`` is passed as a second argument to ``isinstance()``.

    :param types: *Tuple[Type]* – One or more types which the argument must be an instance of.

    Examples:

    .. code-block:: python

        from argscheck import Typed

        # Check if integer or float
        checker = Typed(int, float)

        checker.check(1.234)    # Passes, returns 1.234
        checker.check("1.234")  # Fails, raises TypeError (type is str and not int or float)
    """
    def __init__(self, *types, **kwargs):
        super().__init__(**kwargs)

        if not types:
            raise TypeError(f'{self!r}() expects at least one positional argument.')

        if not all(isinstance(typ, type) for typ in types):
            raise TypeError(f'Argument types={types!r} of {self!r}() is expected to be one or more types.')

        self.types = types

    def __call__(self, name, value):
        passed, value = super().__call__(name, value)
        if not passed:
            return False, value

        if isinstance(value, self.types):
            return True, value
        else:
            return False, TypeError(f'Argument {name}={value!r} is expected to be of type {self.types!r}.')


class Optional(Checker):
    """
    Check if argument is ``None`` or something else, similarly to ``typing.Optional``.

    :param args: *Tuple[CheckerLike]* – Specifies what the argument may be (other than ``None``).
    :param default_value: *Optional[Any]* – If argument is ``None``, it will be replaced by ``default_value``.
    :param default_factory: *Optional[Callable]* – if argument is ``None``, it will be replaced by ``default_factory()``.
        This is useful for setting default values that are of mutable types.
    :param sentinel: *Optional[Any]* – ``x is sentinel`` will be used to tell if the argument is missing, instead of
        ``x is None``.

    Examples:

    .. code-block:: python

        from argscheck import Optional

        # Check if a list, set or None, replace None with a fresh list
        checker = Optional(list, set, default_factory=list)

        checker.check([1, 2, 3])  # Passes, returns [1, 2, 3]
        checker.check({1, 2, 3})  # Passes, returns {1, 2, 3}
        checker.check(None)       # Passes, returns []
        checker.check("string")   # Fails, raises TypeError ("string" is neither None nor a list or a set)
    """
    missing = Sentinel('<MISSING>')

    def __init__(self, *args, default_value=missing, default_factory=missing, sentinel=None, **kwargs):
        super().__init__(**kwargs)

        if default_value is not self.missing and default_factory is not self.missing:
            raise TypeError(f'{self!r}() expects that default_value and default_factory are not both provided.')

        if default_factory is not self.missing and not callable(default_factory):
            raise TypeError(f'{self!r}() expects that if default_factory is provided, it must be a callable.')

        if default_factory is not self.missing:
            self.default_factory = default_factory
        elif default_value is not self.missing:
            self.default_factory = lambda: default_value
        else:
            self.default_factory = lambda: sentinel

        self.checker = self._validate_args(args)
        self.sentinel = sentinel

    def __call__(self, name, value):
        passed, value = super().__call__(name, value)
        if not passed:
            return False, value

        passed, value_ = self.checker(name, value)

        if passed:
            return True, value_
        elif value is self.sentinel:
            return True, self.default_factory()
        else:
            Error = type(value_)

            return False, Error(f'Argument {name}={value!r} is expected to be missing or {self.checker!r}.')


class Comparable(Checker):
    """
    Check if argument correctly compares to other value(s) using any of the following binary operators:
    ``{< | <= | != | == | >= | >}``.

    Comparison need not necessarily be between numeric types, as can be seen in the example below.

    :param args: Used only for compatibility.
    :param lt: *Optional[Any]* – Argument must be less than ``lt``.
    :param le: *Optional[Any]* – Argument must be less than or equal to ``le``.
    :param ne: *Optional[Any]* – Argument must not be equal to ``ne``.
    :param eq: *Optional[Any]* – Argument must be equal to ``eq``.
    :param ge: *Optional[Any]* – Argument must be greater than or equal to ``ge``.
    :param gt: *Optional[Any]* – Argument must be greater than ``gt``.
    :param other_type: *Optional[Union[Type, Tuple[Type]]]* – The above parameters will have to be of this type(s).

    Example:

    .. code-block:: python

        from argscheck import Comparable

        # Check if a strict subset
        checker = Comparable(lt={'a', 'b'})

        checker.check(set())       # Passes, returns set()
        checker.check({'a'})       # Passes, returns {'a'}
        checker.check({'a', 'b'})  # Fails, raises ValueError ({'a', 'b'} is equal to {'a', 'b'})
        checker.check('a')         # Fails, raises TypeError (operator < is not supported between set and str)
    """
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

        # Create comparator functions for the arguments that are not None
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

        # TODO check if bool

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


class One(Checker):
    """
    Check if argument matches exactly one of a set of checkers.

    :param args: *Tuple[CheckerLike]* – At least two checker-like object(s) out of which exactly one must pass.

    Examples:

    .. code-block:: python

        from argscheck import One

        checker = One()
    """
    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)

        if len(args) < 2:
            raise TypeError(f'{self!r}() must be called with at least two positional arguments, got {args!r}.')

        # Validate checker-like positional arguments
        self.checkers = [self._validate_args(arg, name=f'args[{i}]') for i, arg in enumerate(args)]

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
            checkers = ', '.join(map(repr, self.checkers))
            return False, Exception(f'Argument {name}={value!r} is expected to pass exactly one of: {checkers}.')
