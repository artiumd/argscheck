"""
Core
====

This module contains the :class:`.Checker` base class, the :func:`.check_args` function decorator, as well as other
basic checkers that do not correspond to a particular type or protocol.
"""
from functools import wraps
import inspect

from .utils import extend_docstring, partition, join


RAISE_ON_ERROR_DEFAULT = True


def check(checker_like, value, name='', raise_on_error=RAISE_ON_ERROR_DEFAULT):
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
    if not isinstance(raise_on_error, bool):
        raise TypeError(f'check() expects that raise_on_error is bool, got {raise_on_error.__class__.__name__} instead.')

    checker = Checker.from_checker_likes(checker_like)
    result = checker.check(name, value, raise_on_error=raise_on_error)

    if isinstance(result, Wrapper):
        return result
    else:
        passed, new_value = result

        if not raise_on_error:
            return passed, new_value, value
        elif passed:
            return new_value
        else:
            raise new_value


def check_args(function=None, raise_on_error=RAISE_ON_ERROR_DEFAULT):
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
    def decorator(fn):
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
            # Bind arguments to parameters, so we can associate checkers with argument values
            bound = signature.bind(*args, **kwargs)
            bound.apply_defaults()

            # Check each argument for which a checker was defined, then, call original function with checked values
            for name, checker in checkers.items():
                value = bound.arguments[name]
                bound.arguments[name] = check(checker, value, name, raise_on_error=raise_on_error)

            return fn(*bound.args, **bound.kwargs)

        return checked_fn

    if function is None:
        # When applied like @check_args(...)
        return decorator
    else:
        # When applied like @check_args
        return decorator(function)


def validator(checker, name, raise_on_error=RAISE_ON_ERROR_DEFAULT, **kwargs):
    """
    Create a `validator <https://pydantic-docs.helpmanual.io/usage/validators/>`_ for a field in a
    ``pydantic`` model. The validator will perform the checking and conversion by calling the
    :meth:`.Checker.check` method.

    :param name: *str* – Name of field for which validator is created.
    :param kwargs: *Optional* – Passed to ``pydantic.validator`` as-is.
    """
    import pydantic

    return pydantic.validator(name, **kwargs)(lambda value: check(checker, value, name, raise_on_error=raise_on_error))


class Wrapper:
    def __getattr__(self, item):
        return getattr(self.wrapped, item)


class CheckerMeta(type):
    def __new__(mcs, name, bases, attrs, types=(object,), **kwargs):
        # __new__ is only defined to consume `deferred` so it does not get passed to `type.__new__`.
        # Otherwise, an exception is thrown: TypeError: __init_subclass__() takes no keyword arguments
        return super().__new__(mcs, name, bases, attrs, **kwargs)

    def __init__(cls, name, bases, attrs, types=(object,), **kwargs):
        super().__init__(name, bases, attrs, **kwargs)

        if not isinstance(types, tuple) or not all(isinstance(type_, type) for type_ in types):
            raise TypeError(f'`types` must be a tuple of types, got {types} instead.')

        cls.types = types
        extend_docstring(cls)

    def __getitem__(cls, item):
        if isinstance(item, tuple):
            return cls(*item)
        else:
            return cls(item)


class Checker(metaclass=CheckerMeta):
    """
    Base class for all checkers. This is presented mainly for the user-facing methods described below.
    """

    def __repr__(self):
        return type(self).__qualname__

    @classmethod
    def from_checker_likes(cls, value, name='args'):
        if isinstance(value, tuple):
            if len(value) == 1:
                value = value[0]
            elif len(value) > 1:
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
            else:
                pass

        if isinstance(value, Checker):
            return value

        if isinstance(value, type) and issubclass(value, Checker):
            return value()

        if isinstance(value, type):
            return Typed(value)

        raise TypeError(f'{name}={value!r} is a expected to be a checker-like.')

    def expected(self):
        return []

    def check(self, name, value, **kwargs):
        return True, value

    def _assert_not_in_kwargs(self, *names, **kwargs):
        for name in names:
            if name in kwargs:
                raise ValueError(f'{self!r}() got an unexpected argument {name}={kwargs[name]!r}.')

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
        expected = 'EXPECTED: ' + join(", ", self.expected(), on_empty="drop")
        err_msg = '\n'.join([title, actual, expected])

        return err_type(err_msg)


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
            return super().__new__(Checker)
        else:
            return super().__new__(cls)

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)

        if not args:
            self._raise_init_type_error('at least one type must be present', *args)

        if not all(isinstance(arg, type) for arg in args):
            self._raise_init_type_error('only types must be present', *args)

        self.types = args

    def check(self, name, value, **kwargs):
        passed, value = super().check(name, value)
        if not passed:
            return False, value

        if isinstance(value, self.types):
            return True, value
        else:
            return False, self._make_check_error(TypeError, name, value)

    def expected(self):
        s = ', '.join(map(repr, self.types))
        s = f'({s})' if len(self.types) > 1 else s
        s = f'an instance of {s}'

        return super().expected() + [s]


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

    def check(self, name, value, **kwargs):
        passed, value = super().check(name, value)
        if not passed:
            return False, value

        passed_count = 0
        ret_value = None

        # Apply all checkers to value, make sure only one passes
        for checker in self.checkers:
            result = checker.check(name, value)

            if isinstance(result, Wrapper):
                raise NotImplementedError(f'{self!r} does not support nesting deferred checkers such as {checker!r}.')

            passed, ret_value_ = result
            if passed:
                passed_count += 1
                ret_value = ret_value_

        # The `One` checker passes only if exactly one of its checkers passes
        if passed_count == 1:
            return True, ret_value
        else:
            return False, self._make_check_error(Exception, name, value)

    def expected(self):
        indent = ' ' * len('EXPECTED: ')
        options = [', '.join(checker.expected()) for checker in self.checkers]
        options = [f'{indent}{i}. {option}' for i, option in enumerate(options, start=1)]
        s = 'exactly one of the following:\n' + '\n'.join(options)

        return super().expected() + [s]
