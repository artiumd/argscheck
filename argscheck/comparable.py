from argscheck import Checker


class _Comparer:
    def __init__(self, other):
        self.other = other


class _LessThanComparer(_Comparer):
    name = 'less than'

    def __call__(self, value):
        return value < self.other


class _LessEqualComparer(_Comparer):
    name = 'less than or equal to'

    def __call__(self, value):
        return value <= self.other


class _GreaterThanComparer(_Comparer):
    name = 'greater than'

    def __call__(self, value):
        return value > self.other


class _GreaterEqualComparer(_Comparer):
    name = 'greater than or equal to'

    def __call__(self, value):
        return value >= self.other


class _EqualComparer(_Comparer):
    name = 'equal to'

    def __call__(self, value):
        return value == self.other


class _NotEqualComparer(_Comparer):
    name = 'not equal to'

    def __call__(self, value):
        return value != self.other


class _Descriptor:
    excludes = set()
    greater_than = set()
    less_than = set()
    Comparer = None

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

            value = self.Comparer(value)

        obj.__dict__[self.name] = value


class _LessThanDescriptor(_Descriptor):
    excludes = {'le', 'eq'}
    greater_than = {'gt', 'ge'}
    Comparer = _LessThanComparer


class _LessEqualDescriptor(_Descriptor):
    excludes = {'lt', 'eq'}
    greater_than = {'gt', 'ge'}
    Comparer = _LessEqualComparer


class _GreaterThanDescriptor(_Descriptor):
    excludes = {'ge', 'eq'}
    less_than = {'lt', 'le'}
    Comparer = _GreaterThanComparer


class _GreaterEqualDescriptor(_Descriptor):
    excludes = {'gt', 'eq'}
    less_than = {'lt', 'le'}
    Comparer = _GreaterEqualComparer


class _EqualDescriptor(_Descriptor):
    excludes = {'lt', 'le', 'gt', 'ge', 'ne'}
    Comparer = _EqualComparer


class _NotEqualDescriptor(_Descriptor):
    excludes = {'eq'}
    Comparer = _NotEqualComparer


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
    lt = _LessThanDescriptor()
    le = _LessEqualDescriptor()
    gt = _GreaterThanDescriptor()
    ge = _GreaterEqualDescriptor()
    eq = _EqualDescriptor()
    ne = _NotEqualDescriptor()

    def __init__(self, *args, lt=None, le=None, ne=None, eq=None, ge=None, gt=None, other_type=object, **kwargs):
        super().__init__(*args, **kwargs)

        # `other_type` must be a type or tuple of types
        if not isinstance(other_type, tuple):
            other_type = (other_type,)
        if not all(isinstance(item, type) for item in other_type):
            self._raise_init_type_error('must be a type or tuple of types', other_type=other_type)

        self.other_type = other_type

        # Set comparators
        self.lt, self.le, self.ne, self.eq, self.ge, self.gt = lt, le, ne, eq, ge, gt

    def check(self, name, value, **kwargs):
        passed, value = super().check(name, value)
        if not passed:
            return False, value

        for comparator in (self.lt, self.le, self.ne, self.eq, self.ge, self.gt):
            if comparator is not None:
                try:
                    result = comparator(value)
                except TypeError:
                    return False, self._make_check_error(TypeError, name, value)

                if not result:
                    return False, self._make_check_error(ValueError, name, value)

        return True, value

    def expected(self):
        comparators = (self.lt, self.le, self.ne, self.eq, self.ge, self.gt)
        expected = [f'{comparator.name} {comparator.other!r}' for comparator in comparators if comparator is not None]
        expected = ', '.join(expected)

        return super().expected() + [expected]
