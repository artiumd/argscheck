"""
Comparable
==========

This page documents the :class:`.Comparable` checker.
"""

import operator

from argscheck import Checker


class _Descriptor:
    def __init__(self, comp_op, excludes=None, greater_than=None, less_than=None, long_name=None):
        self.comp_op = comp_op
        self.excludes = set() if excludes is None else excludes
        self.greater_than = set() if greater_than is None else greater_than
        self.less_than = set() if less_than is None else less_than
        self.long_name = long_name

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, owner=None):
        return obj.__dict__.get(self.name, None)

    def __set__(self, obj, value):
        if value is not None:
            if not isinstance(value, obj.other_type):
                obj._raise_init_type_error(f'must have type {obj.other_type!r} if present', **{self.name: value})

            for other_name in self.excludes:
                other_value = getattr(obj, other_name)

                if other_value is not None:
                    obj._raise_init_type_error('must not be both present', **{self.name: value, other_name: other_value.other})

            for other_name in self.greater_than:
                other_value = getattr(obj, other_name)

                if other_value is not None and value < other_value.other:
                    obj._raise_init_value_error(f'{self.name} must be greater than {other_name}',
                                                **{self.name: value, other_name: other_value.other})

            for other_name in self.less_than:
                other_value = getattr(obj, other_name)

                if other_value is not None and value > other_value.other:
                    obj._raise_init_value_error(f'{self.name} must be less than {other_name}',
                                                **{self.name: value, other_name: other_value.other})

            value = _Comparer(value, self.long_name, self.comp_op)

        obj.__dict__[self.name] = value


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

    lt = _Descriptor(operator.lt, excludes={'le', 'eq'}, greater_than={'gt', 'ge'}, long_name='less than')
    le = _Descriptor(operator.le, excludes={'lt', 'eq'}, greater_than={'gt', 'ge'}, long_name='less than or equal to')
    gt = _Descriptor(operator.gt, excludes={'ge', 'eq'}, less_than={'lt', 'le'}, long_name='greater than')
    ge = _Descriptor(operator.ge, excludes={'gt', 'eq'}, less_than={'lt', 'le'}, long_name='greater than or equal to')
    eq = _Descriptor(operator.eq, excludes={'lt', 'le', 'gt', 'ge', 'ne'}, long_name='equal to')
    ne = _Descriptor(operator.ne, excludes={'eq'}, long_name='not equal to')

    def __init__(self, *args, lt=None, le=None, ne=None, eq=None, ge=None, gt=None, other_type=object, **kwargs):
        super().__init__(*args, **kwargs)

        # `other_type` must be a type or tuple of types
        if not isinstance(other_type, tuple):
            other_type = (other_type,)
        if not all(isinstance(item, type) for item in other_type):
            self._raise_init_type_error('must be a type or tuple of types', other_type=other_type)

        self.other_type = other_type
        self.lt, self.le, self.ne, self.eq, self.ge, self.gt = lt, le, ne, eq, ge, gt

    def __lt__(self, other):
        self.lt = other

        return self

    def __gt__(self, other):
        self.gt = other

        return self

    def __le__(self, other):
        self.le = other

        return self

    def __ge__(self, other):
        self.ge = other

        return self

    def __ne__(self, other):
        self.ne = other

        return self

    def __eq__(self, other):
        self.eq = other

        return self

    def check(self, name, value, **kwargs):
        passed, value = super().check(name, value)
        if not passed:
            return False, value

        for comparator in self._comparators():
            if comparator is not None:
                try:
                    result = comparator(value)
                except TypeError:
                    return False, self._make_check_error(TypeError, name, value)

                if not result:
                    return False, self._make_check_error(ValueError, name, value)

        return True, value

    def expected(self):
        expected = [f'{comparator.long_name} {comparator.other!r}' for comparator in self._comparators()]
        expected = ', '.join(expected)

        return super().expected() + [expected]

    def _comparators(self):
        for comparator in (self.lt, self.le, self.ne, self.eq, self.ge, self.gt):
            if comparator is not None:
                yield comparator


class _Comparer:
    def __init__(self, other, long_name, comp_op):
        self.other = other
        self.long_name = long_name
        self.comp_op = comp_op

    def __call__(self, value):
        return self.comp_op(value, self.other)
