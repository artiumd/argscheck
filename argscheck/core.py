"""
Core
====

This module contains the :class:`.Checker` base class, the :func:`.check_args` function decorator, as well as other
basic checkers that do not correspond to a particular type or protocol.
"""
import operator
from functools import partial, wraps
import inspect

from .utils import extend_docstring, partition, join


def check_args(fn):
    """
    A decorator, that when applied to a function:

    1. Gathers checkers from parameter annotations in function's signature.
    2. Performs argument checking (and possibly conversion) on each function call.

    :Example:

    .. code-block:: python

        from argscheck import check_args, Number, Float

        # Check if a, b are numbers and alpha is a float in range [0,1]
        @check_args
        def convex_sum(a: Number, b: Number, alpha: Float(ge=0.0, le=1.0)):
            return alpha * a + (1.0 - alpha) * b

        convex_sum(0, 2, 0.0)    # Passes, returns 2.0
        convex_sum(0, 2, 1.1)    # Fails, raises ValueError (1.1 is greater than 1.0)
        convex_sum(0, [2], 0.5)  # Fails, raises TypeError ([2] is not a number)

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
    Base class for all checkers. This is presented mainly for the user-facing methods described below.
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
                others.append(Typed(*types))
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

    def _assert_not_in_kwargs(self, *names, **kwargs):
        for name in names:
            if name in kwargs:
                raise ValueError(f'{self!r}() got an unexpected argument {name}={kwargs[name]!r}.')

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

    def _raise_init_error(self, err_type, desc, *args, **kwargs):
        args = [f'{value!r}' for value in args]
        kwargs = [f'{name}={value!r}' for name, value in kwargs.items()]
        arguments = ', '.join(args + kwargs)
        err_msg = f'{self!r}({arguments}): {desc}.'

        raise err_type(err_msg)

    def _raise_init_type_error(self, desc, *args, **kwargs):
        self._raise_init_error(TypeError, desc, *args, **kwargs)

    def _raise_init_value_error(self, desc, *args, **kwargs):
        self._raise_init_error(ValueError, desc, *args, **kwargs)

    def _make_check_error(self, err_type, name, value):
        title = join(' ', ['encountered an error while checking', name], on_empty='drop') + ':'
        actual = f'ACTUAL: {value!r}'
        expected = 'EXPECTED: ' + join(", ", self.expected_str(), on_empty="drop")
        err_msg = '\n'.join([title, actual, expected])

        return err_type(err_msg)

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
        Create a `validator <https://pydantic-docs.helpmanual.io/usage/validators/>`_ for a field in a
        ``pydantic`` model. The validator will perform the checking and conversion by calling the
        :meth:`.Checker.check` method.

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
        # In case ``Typed(*types)`` and ``types`` contains ``object``, return a ``Checker`` instance, which will always
        # pass without the need to call ``isinstance()``.
        if cls is Typed and object in args:
            return object.__new__(Checker)
        else:
            return object.__new__(cls)

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)

        if not args:
            self._raise_init_type_error('at least one type must be present', *args)

        if not all(isinstance(arg, type) for arg in args):
            self._raise_init_type_error('only types must be present', *args)

        self.types = args

    def expected_str(self):
        s = ', '.join(map(repr, self.types))
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
            return False, self._make_check_error(TypeError, name, value)


class Comparable(Checker):
    """
    Check if ``x`` correctly compares to other value(s) using any of the following binary operators:
    ``<``, ``<=``, ``!=``, ``==``, ``>=`` or ``>``.

    Comparison need not necessarily be between numeric types, as can be seen in the example below.

    :param lt: *Optional[Any]* – Check if ``x < lt``.
    :param le: *Optional[Any]* – Check if ``x <= le``.
    :param ne: *Optional[Any]* – Check if ``x != ne``.
    :param eq: *Optional[Any]* – Check if ``x == eq``.
    :param ge: *Optional[Any]* – Check if ``x >= ge``.
    :param gt: *Optional[Any]* – Check if ``x > gt``.
    :param other_type: *Optional[Union[Type, Tuple[Type]]]* – If provided, restricts the types to which ``x`` can
       be compared, e.g. ``other_type=int`` with ``ne=1.0`` will raise a ``TypeError`` (because ``1.0`` is not an
       ``int``).

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

        # `other_type` must be a type or tuple of types
        if not isinstance(other_type, tuple):
            other_type = (other_type,)
        if not all(isinstance(item, type) for item in other_type):
            self._raise_init_type_error('must be a type or tuple of types', other_type=other_type)

        # Check "other" argument types according to `other_type`
        for name, value in others.items():
            if not isinstance(value, other_type):
                other_type = other_type[0] if len(other_type) == 1 else other_type
                self._raise_init_type_error(f'must have type {other_type!r} if present', **{name: value})

        # `lt` and `le` are mutually exclusive
        if 'lt' in others and 'le' in others:
            self._raise_init_type_error('must not be both present', lt=lt, le=le)

        # `ge` and `gt` are mutually exclusive
        if 'ge' in others and 'gt' in others:
            self._raise_init_type_error('must not be both present', ge=ge, gt=gt)

        # `eq` exclude all other arguments
        if 'eq' in others and len(others) > 1:
            del others['eq']
            self._raise_init_type_error(f'must not be present if eq={eq!r} is present', **others)

        # Check that lower bound is indeed lower than upper bound (if both are provided)
        lb = ('ge', ge) if ge is not None else ('gt', gt)
        ub = ('le', le) if le is not None else ('lt', lt)
        if (lb[1] is not None) and (ub[1] is not None) and (lb[1] > ub[1]):
            self._raise_init_value_error('lower bound must be lower than upper bound', **dict([lb, ub]))

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
            return False, self._make_check_error(TypeError, name, value)

        if result:
            return True, value
        else:
            return False, self._make_check_error(ValueError, name, value)

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
            self._raise_init_type_error('must be called with at least two positional arguments', *args)

        # Partition tuple into non-Checker types and everything else
        types, others = partition(args, lambda x: isinstance(x, type) and not issubclass(x, Checker))

        if not others:
            self._raise_init_type_error('must not contain only plain types. in this case `Typed` should be used', *args)

        if types:
            others.append(Typed(*types))

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
            return False, self._make_check_error(Exception, name, value)
