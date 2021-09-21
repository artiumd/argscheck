"""
Core
====
"""
import operator
from functools import partial, wraps
import inspect

from .utils import Sentinel, extend_docstring, partition


def check_args(fn):
    """
    Decorator that when applied to a function:

    1. Gathers checkers from parameter annotations in function's signature.
    2. Performs argument checking (and possibly conversion) on each function call.
    """
    checkers = {}

    # Extract signature, iterate over parameters and create checkers from annotations
    signature = inspect.signature(fn)

    for name, parameter in signature.parameters.items():
        annotation = parameter.annotation

        # Skip parameters without annotations
        if annotation == parameter.empty:
            continue

        checkers[name] = Checker.from_checker_likes(annotation, f'{fn.__name__}({name})')

    # Build a function that performs argument checking, then, calls original function
    @wraps(fn)
    def checked_fn(*args, **kwargs):
        # Bind arguments to parameters so we can associate checkers with argument values
        bound_args = signature.bind(*args, **kwargs)
        bound_args.apply_defaults()

        # Check each argument for which a checker was defined, then, call original function with checked values
        for name, checker in checkers.items():
            value = bound_args.arguments[name]
            bound_args.arguments[name] = checker._check(name, value)

        return fn(*bound_args.args, **bound_args.kwargs)

    return checked_fn


class CheckerMeta(type):
    def __init__(cls, name, bases, attrs, **kwargs):
        super().__init__(name, bases, attrs, **kwargs)
        extend_docstring(cls)


class Checker(metaclass=CheckerMeta):
    """
    Base class for all checkers.
    """
    def __repr__(self):
        return type(self).__qualname__

    def __call__(self, name, value):
        return True, value

    @classmethod
    def from_checker_likes(cls, value, name='args'):
        if isinstance(value, tuple) and len(value) == 1:
            return cls.from_checker_likes(value[0], name=f'{name}[0]')

        if isinstance(value, tuple) and len(value) > 1:
            # Partition tuple into non-Checker types and everything else
            types, others = partition(value, lambda x: isinstance(x, type) and not issubclass(x, Checker))

            if types and others:
                others.insert(0, Typed(*types))
                checker = One(*others)
            elif types:
                checker = Typed(*types)
            else:
                checker = One(*others)

            return checker

        if isinstance(value, Checker):
            return value

        if isinstance(value, type) and issubclass(value, Checker):
            return value()

        if isinstance(value, type):
            return Typed(value)

        raise TypeError(f'{name}={value!r} is a expected to be a checker-like.')

    def _resolve_name_value(self, *args, **kwargs):
        # Make sure method is called properly and unpack argument's name and value
        if len(args) + len(kwargs) != 1:
            raise TypeError(f'{self!r}.check() must be called with a single positional or keyword argument.'
                            f' Got {len(args)} positional arguments and {len(kwargs)} keyword arguments.')
        if args:
            return '', args[0]
        else:
            return next(iter(kwargs.items()))

    def expected_str(self):
        return []

    def _make_error(self, err_type, name, value):
        title = 'encountered an error while checking'

        if name != '':
            title += f' `{name}`'

        title += ':\n'

        actual = f'ACTUAL: {value!r}\n'
        expected = f'EXPECTED: {", ".join(self.expected_str())}'

        return err_type(title + actual + expected)

    def _check(self, name, value):
        # Perform argument checking. If passed, return (possibly converted) value, otherwise, raise the returned
        # exception.
        passed, value_or_excp = self(name, value)

        if passed:
            return value_or_excp
        else:
            raise value_or_excp

    def check(self, *args, **kwargs):
        """
        Check an argument (and possibly convert it, depending on the particular checker instance).

        A call to ``check()`` will have one of two possible outcomes:

        1. Check passes, the checked (and possibly converted) argument will be returned.
        2. Check fails, an appropriate exception with an error message will be raised.

        Also, there are two possible calling signatures:

        .. code-block:: python

            checker.check(value)
            checker.check(name=value)

        The only difference is that in the second call, ``name`` will appear in the error message in case the check
        fails.
        """
        name, value = self._resolve_name_value(*args, **kwargs)

        return self._check(name, value)

    def validator(self, name, **kwargs):
        """
        Create a validator for a field in a ``pydantic`` model. The validator will perform the checking and conversion
        by calling the ``check()`` method.

        :param name: *str* – Name of field for which validator is created.
        :param kwargs: *Optional* – Passed to ``pydantic.validator`` as-is.
        """
        import pydantic

        return pydantic.validator(name, **kwargs)(lambda value: self._check(name, value))


class Typed(Checker):
    """
    Check if ``x`` is an instance of a given type (or types) using ``isinstance(x, args)``.

    :param args: *Tuple[Type]* – One or more types.

    :Example:

    .. code-block:: python

        from argscheck import Typed

        # Check if integer or float
        checker = Typed(int, float)

        checker.check(1.234)    # Passes, returns 1.234
        checker.check("1.234")  # Fails, raises TypeError (type is str and not int or float)

    """
    def __new__(cls, *args, **kwargs):
        if cls is Typed and object in args:
            return object.__new__(Checker)
        else:
            return object.__new__(cls)

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)

        if not args:
            raise TypeError(f'{self!r}() expects at least one positional argument.')

        if not all(isinstance(arg, type) for arg in args):
            raise TypeError(f'Argument args={args!r} of {self!r}() is expected to be one or more types.')

        self.types = args

    def expected_str(self):
        s = ", ".join(map(repr, self.types))
        s = f'({s})' if len(self.types) > 1 else s
        s = f'an instance of {s}'

        return super().expected_str() + [s]

    def __call__(self, name, value):
        passed, value = super().__call__(name, value)
        if not passed:
            return False, value

        if isinstance(value, self.types):
            return True, value
        else:
            return False, self._make_error(TypeError, name, value)


class Optional(Checker):
    """
    Check if ``x`` is ``None`` or something else, similarly to ``typing.Optional``.

    :param args: *Tuple[CheckerLike]* – Specifies what ``x`` may be (other than ``None``).
    :param default_value: *Optional[Any]* – If ``x is None``, it will be replaced by ``default_value``.
    :param default_factory: *Optional[Callable]* – if ``x is None``, it will be replaced by ``default_factory()``.
        This is useful for setting default values that are of mutable types.
    :param sentinel: *Optional[Any]* – ``x is sentinel`` will be used to determine if the ``x`` is missing, instead of
        ``x is None``.

    :Example:

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

        self.checker = Checker.from_checker_likes(args)
        self.sentinel = sentinel

    def expected_str(self):
        return super().expected_str() + ['missing or'] + self.checker.expected_str()

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
            return False, self._make_error(type(value_), name, value)


class Comparable(Checker):
    """
    Check if ``x`` correctly compares to other value(s) using any of the following binary operators:
    ``{< | <= | != | == | >= | >}``.

    Comparison need not necessarily be between numeric types, as can be seen in the example below.

    :param lt: *Optional[Any]* – Check if ``x < lt``.
    :param le: *Optional[Any]* – Check if ``x <= le``.
    :param ne: *Optional[Any]* – Check if ``x != ne``.
    :param eq: *Optional[Any]* – Check if ``x == eq``.
    :param ge: *Optional[Any]* – Check if ``x >= ge``.
    :param gt: *Optional[Any]* – Check if ``x > gt``.
    :param other_type: *Optional[Union[Type, Tuple[Type]]]* – If provided, restricts the types to which ``x`` can
       be compared, e.g. ``other_type=int`` with ``ne=1.0`` will raise a ``TypeError``.

    :Example:

    .. code-block:: python

        from argscheck import Comparable

        # Check if a strict subset
        checker = Comparable(lt={'a', 'b'})

        checker.check(set())       # Passes, returns set()
        checker.check({'a'})       # Passes, returns {'a'}
        checker.check({'a', 'b'})  # Fails, raises ValueError ({'a', 'b'} is equal to {'a', 'b'})
        checker.check('a')         # Fails, raises TypeError (< is not supported between set and str)
    """
    comp_fns = dict(lt=operator.lt, le=operator.le, ne=operator.ne, eq=operator.eq, ge=operator.ge, gt=operator.gt)
    comp_names = dict(lt='less than', le='less than or equal to', ne='not equal to', eq='equal to',
                      ge='greater than or equal to', gt='greater than')

    def __init__(self, *args, lt=None, le=None, ne=None, eq=None, ge=None, gt=None, other_type=object, **kwargs):
        super().__init__(*args, **kwargs)

        # Arrange arguments in a dictionary for convenience, keep only those that are not None
        others = dict(lt=lt, le=le, ne=ne, eq=eq, ge=ge, gt=gt)
        others = {name: value for name, value in others.items() if value is not None}

        # Check that arguments are numbers or None
        for name, value in others.items():
            if not isinstance(value, other_type):
                raise TypeError(f'Argument {name}={value!r} of {self!r}() must be {other_type!r} or None.')

        if 'lt' in others and 'le' in others:
            raise TypeError(f'Arguments lt={lt!r} and le={le!r} of {self!r}() must not be both provided.')

        if 'ne' in others and 'eq' in others:
            raise TypeError(f'Arguments ne={ne!r} and eq={eq!r} of {self!r}() must not be both provided.')

        if 'ge' in others and 'gt' in others:
            raise TypeError(f'Arguments ge={ge!r} and gt={gt!r} of {self!r}() must not be both provided.')

        if 'eq' in others and len(others) > 1:
            raise TypeError(f'Argument eq={eq!r} excludes all other arguments of {self!r}.')

        # Check that lower bound is indeed lower than upper bound (if both are provided)
        lb = ge if ge is not None else gt
        ub = le if le is not None else lt
        if (lb is not None) and (ub is not None) and (lb > ub):
            raise ValueError(f'Lower bound {lb!r} of {self!r} must be lower than the upper bound {ub!r}.')

        # Create comparator functions for the arguments that are not None
        self.comparators = [partial(self._compare, other=other, comp_fn=self.comp_fns[name])
                            for name, other
                            in others.items()]

        # Build the "expected" string
        expected = [f'{self.comp_names[name]} {other!r}' for name, other in others.items()]
        self._expected_str = ', '.join(expected)

    def _compare(self, name, value, other, comp_fn):
        # Compare value, if comparison fails, return the caught exception
        try:
            result = comp_fn(value, other)
        except TypeError:
            return False, self._make_error(TypeError, name, value)

        if result:
            return True, value
        else:
            return False, self._make_error(ValueError, name, value)

    def expected_str(self):
        return super().expected_str() + [self._expected_str]

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
    Check if ``x`` matches exactly one of a set of checkers.

    :param args: *Tuple[CheckerLike]* – At least two checker-like object(s) out of which exactly one must pass.

    :Example:

    .. code-block:: python

        from argscheck import One

        checker = One()
    """
    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)

        if len(args) < 2:
            raise TypeError(f'{self!r}() must be called with at least two positional arguments, got {args!r}.')

        # Partition tuple into non-Checker types and everything else
        types, others = partition(args, lambda x: isinstance(x, type) and not issubclass(x, Checker))

        if not others:
            raise TypeError(f'`One` checker got only plain types: {args}, in this case `Typed` should be used instead.')

        if types:
            others.insert(0, Typed(*types))

        # Validate checker-like positional arguments
        self.checkers = [Checker.from_checker_likes(other, name=f'args[{i}]') for i, other in enumerate(others)]

    def expected_str(self):
        indent = ' ' * len('EXPECTED: ')
        options = [', '.join(checker.expected_str()) for checker in self.checkers]
        options = [f'{indent}{i}. {option}' for i, option in enumerate(options, start=1)]
        s = 'exactly one of the following:\n' + '\n'.join(options)

        return super().expected_str() + [s]

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
            return False, self._make_error(Exception, name, value)
