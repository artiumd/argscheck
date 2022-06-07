"""
Core
====

This section documents the functions available to perform argument checking.

These can be used with checker-likes (types or tuples of types) or with checkers from the other sections to check for
more complex conditions.

Also present is the documentation of the :class:`.One` checker.
"""

import sys
from functools import wraps
import inspect

from .utils import extend_docstring, partition, join


# Reusable default value for raise_on_error parameter
RAISE_ON_ERROR_DEFAULT = True


def check(checker_like, value, name='', raise_on_error=RAISE_ON_ERROR_DEFAULT):
    """
    Check an argument (and possibly convert it).

    The default behaviour is:

    1. If check passes, the checked (and possibly converted) argument will be returned.
    2. If check fails, an appropriate exception with an error message will be raised.

    :Example:

    .. code-block:: python

        from argscheck import check


        check(int, 1)      # Passes, 1 is returned.
        check(int, 'one')  # Fails, a TypeError is raised.

    Users who prefer to handle the check failure on their own, can use the alternative behaviour by passing
    `raise_on_error=False`.

    In this case, exceptions are never raised and the return value is `(passed, new_value, old_value)`:

    * `passed` - is a boolean indicating whether the check passed or not.
    * `new_value` - If `passed`, this is the checked (and possibly converted) argument value. Otherwise, this is the exception that would have been raised by the default behaviour.
    * `old_value` - is the same object `value` passed to `check()`.

    :Example:

    .. code-block:: python

        from argscheck import check


        passed, value, _ = check(int, 1, raise_on_error=False)      # passed is True, value is 1.
        passed, value, _ = check(int, 'one', raise_on_error=False)  # passed is False, value is a TypeError.

    :param checker_like: *CheckerLike* – Describes the check performed on `value`.
    :param value: *Any* - The value of the argument being checked.
    :param name: *Optional[str]* - Optional name of the argument being checked. Will be used in error messages.
    :param raise_on_error: *bool* - Whether to use the default or the alternative behaviour of this function.
    """

    # raise_on_error must be a boolean
    if not isinstance(raise_on_error, bool):
        raise TypeError(f'check() expects that raise_on_error is bool, got {raise_on_error.__class__.__name__} instead.')

    # Transform checker-like to checker and apply it to the argument's value
    checker = Checker.from_checker_likes(checker_like)
    result = checker.check(name, value, raise_on_error=raise_on_error)

    # If a wrapper is returned, just return it (checking will take place on evaluation). Otherwise, return or raise
    # according to the logic described in the docstring
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
    A decorator that makes a function (or a method) automatically perform argument checking each time its called.

    The checker used on each parameter is extracted from its annotation in the function definition statement
    (parameters without annotation will not be checked).

    :Example:

    .. code-block:: python

        from argscheck import check_args, Number, Float


        @check_args
        def convex_sum(a: Number, b: Number, alpha: (0.0 <= Float) <= 1.0):
            return alpha * a + (1.0 - alpha) * b


        convex_sum(0, 2, 0.0)    # Passes, 2.0 is returned
        convex_sum(0, 2, 1.1)    # Fails, a ValueError is raised (1.1 is greater than 1.0)
        convex_sum(0, [2], 0.5)  # Fails, a TypeError is raised ([2] is not a number)

    Just like with :func:`.check`, we may prefer to handle errors ourselves, in which case we can use the alternative
    behaviour by passing a flag to the decorator.

    :Example:

    .. code-block:: python

        import logging
        from argscheck import check_args, Number, Float


        @check_args(raise_on_error=False)
        def convex_sum(a: Number, b: Number, alpha: (0.0 <= Float) <= 1.0):
            # Check a
            passed, exception, a = a
            if not passed:
                logging.critical('Error in a=%s argument of convex_sum: %s', a, exception)
                raise exception

            # Check b
            passed, exception, b = b
            if not passed:
                logging.critical('Error in b=%s argument of convex_sum: %s', b, exception)
                raise exception

            # Check alpha
            passed, exception, alpha = alpha
            if not passed:
                logging.critical('Error in alpha=%s argument of convex_sum: %s', alpha, exception)
                raise exception

            return alpha * a + (1.0 - alpha) * b


        convex_sum(0, 2, 0.0)    # Passes, 2.0 is returned
        convex_sum(0, 2, 1.1)    # Fails, a ValueError is raised (1.1 is greater than 1.0)
        convex_sum(0, [2], 0.5)  # Fails, a TypeError is raised ([2] is not a number)
    """

    def decorator(fn):
        checkers = {}

        # Extract signature, iterate over parameters and create checkers from annotations
        signature = inspect.signature(fn)

        for name, parameter in signature.parameters.items():
            annotation = parameter.annotation

            # Skip parameters without annotations
            if annotation is parameter.empty:
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
    ``pydantic`` model. The validator will perform the checking and conversion by internally calling the
    :func:`.check` function.

    :Example:

    .. code-block:: python

        from typing import Any

        from pydantic import BaseModel
        from argscheck import Optional


        class UserModel(BaseModel):
            items: Any
            check_items = validator(Optional(dict, default_factory=dict), 'items')


        UserModel(items={'a': 1, 'b': 2}).items  # Passes, {'a': 1, 'b': 2} is returned
        UserModel(items=None).items              # Passes, {} is returned
        UserModel(items=[1, 2]).items            # Fails, a TypeError is raised

    :param checker: *CheckerLike* - Describes the check that will be performed on the field.
    :param name: *str* – Name of field for which validator is created.
    :param raise_on_error: *bool* – See :func:`.check`.
    :param kwargs: *Optional* – Passed to ``pydantic.validator`` as-is.
    """

    import pydantic

    return pydantic.validator(name, **kwargs)(lambda value: check(checker, value, name, raise_on_error=raise_on_error))


class Wrapper:
    """
    Base class to identify deferred checkers i.e. checkers for which calling :func:`.check` with some value only returns
    a wrapper around that value. Actual checking will be done as items are consumed from that wrapper.

    :meta private:
    """

    def __getattr__(self, item):
        """Base class also provides the wrapping functionality. Looking up members looks up in the wrapped object if
        they are not found on the Wrapper instance itself."""
        return getattr(self.wrapped, item)


class CheckerMeta(type):
    """
    Metaclass for the Checker class.

    :meta private:
    """

    def __new__(mcs, name, bases, attrs, types=(object,), **kwargs):
        # __new__ is only defined to consume `types` so it does not get passed to `type.__new__`.
        # Otherwise, an exception is thrown: TypeError: __init_subclass__() takes no keyword arguments
        return super().__new__(mcs, name, bases, attrs, **kwargs)

    def __init__(cls, name, bases, attrs, types=(object,), **kwargs):
        super().__init__(name, bases, attrs, **kwargs)

        # Validate and set types. It is used by some sub-subclasses of Typed to allow passing different types to
        # Typed.__init__() without having to re-implement __init__().
        if not isinstance(types, tuple) or not all(isinstance(type_, type) for type_ in types):
            raise TypeError(f'`types` must be a tuple of types, got {types} instead.')

        cls.types = types

        # Extend the class docstring by gathering parameters from all of its base classes
        extend_docstring(cls)

    def __getitem__(cls, item):
        """This allows instantiation of checker objects in a typing style e.g.
        Optional[Set[str]] instead of Optional(Set(str)). With this method however, it is not possible to pass any
        named arguments."""

        if isinstance(item, tuple):
            return cls(*item)
        else:
            return cls(item)

    """
    Comparison methods used for cleaner instantiation of Comparable subclasses e.g. Number < 3 instead of Number() < 3.
    """

    def __lt__(cls, other):
        return cls(lt=other)

    def __gt__(cls, other):
        return cls(gt=other)

    def __le__(cls, other):
        return cls(le=other)

    def __ge__(cls, other):
        return cls(ge=other)

    def __ne__(cls, other):
        return cls(ne=other)

    # Workaround: when building sphinx docs, CheckerMeta.__eq__ gets called and breaks the build
    if 'sphinx' not in sys.modules:
        def __eq__(cls, other):
            return cls(eq=other)


class Checker(metaclass=CheckerMeta):
    """
    Base class for all checkers.

    :meta private:
    """

    def __repr__(self):
        return type(self).__qualname__

    @classmethod
    def from_checker_likes(cls, value, name='args'):
        """
        Factory method for creating a checker instance from a checker like object.

        :param value: *CheckerLike* - Checker like object.
        :param name: *str* - Name of argument corresponding to value, used in error message.
        :return: *Checker*
        :raise: TypeError. If value can not be converted to a checker.
        """

        if isinstance(value, tuple):
            if len(value) == 1:
                value = value[0]
            elif len(value) > 1:
                # Partition tuple into plain types and everything else
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
        """
        Returns a list of strings that describe all conditions that the checked value must satisfy in order for the
        check to pass.

        The expected() method typically works by cooperative inheritance and this here is the end of the super() calls
        chain.

        :return: *List[str]*

        :meta private:
        """

        return []

    def check(self, name, value, **kwargs):
        """
        The main method of the Checker class, does the actual argument checking.

        The check() method typically works by cooperative inheritance and this here is the end of the super() calls
        chain.

        :param name: *str* - The name of the argument being checked. Used in error messages.
        :param value: *Any* - The value of the argument being checked.
        :param kwargs: Additional argument passed to the top level caller (typically check(), check_args() or
            validator()), those may be needed in some cases of checker composition when the check() method calls the
            check() function.
        :return: Tuple[bool, Any]. Returns a tuple (passed, value). passed indicates whether the check passed or not.
            If check passed, then value is the (possibly converted) checked value, otherwise it is an exception that
            explains why the check failed.

        :meta private:
        """

        return True, value

    def _assert_not_in_kwargs(self, *names, **kwargs):
        """
        Utility method for validating kwargs argument of calls to check method.

        If any name in names is in kwargs, an error is raised.
        """
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

    :meta private:
    """

    def __new__(cls, *args, **kwargs):
        """
        Small optimization: In case Typed(*types) and types contains object, the check should always pass (because
        everything is an instance of object).

        So in this case we can instead return a base Checker instance (always passes) and save the call ot isinstance
        and super().check().
        """

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
        types = ', '.join(map(repr, self.types))
        types = f'({types})' if len(self.types) > 1 else types
        expected = f'an instance of {types}'

        return super().expected() + [expected]


class One(Checker):
    """
    Check if ``x`` matches **exactly one** of a set of checkers.

    :param args: *Tuple[CheckerLike]* – At least two checker-like object(s) out of which exactly one must pass.

    :Example:

    .. code-block:: python

        from argscheck import check, One


        check(One(list, tuple), [])  # Passes, [] is returned
        check(One(list, tuple), {})  # Fails, a TypeError is raised

        # Can also be used with a shorthand initialization
        check((list, tuple), [])  # Passes, [] is returned
    """
    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)

        if len(args) < 2:
            self._raise_init_type_error('must be called with at least two positional arguments', *args)

        # Partition tuple into plain types and everything else
        types, others = partition(args, lambda x: isinstance(x, type) and not issubclass(x, Checker))

        if not others:
            self._raise_init_type_error('must not contain only plain types. Use a tuple of types instead of One', *args)

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
        expected = 'exactly one of the following:\n' + '\n'.join(options)

        return super().expected() + [expected]
