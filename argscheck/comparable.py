import operator
from functools import partial

from argscheck import Checker


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

    def check(self, name, value, **kwargs):
        passed, value = super().check(name, value)
        if not passed:
            return False, value

        for comparator in self.comparators:
            passed, value = comparator(name, value)
            if not passed:
                return False, value

        return True, value

    def expected(self):
        return super().expected() + [self._expected_str]

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
