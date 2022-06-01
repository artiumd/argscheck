from .core import Checker, Wrapper
from .utils import Sentinel


class Optional(Checker):
    """
    Check if ``x`` is ``None`` or something else, similarly to ``typing.Optional``.

    :param args: *Tuple[CheckerLike]* – Specifies what ``x`` may be (other than ``None``).
    :param default_value: *Optional[Any]* – If ``x is None``, it will be replaced by ``default_value``.
    :param default_factory: *Optional[Callable]* – if ``x is None``, it will be replaced by a value freshly returned
        from ``default_factory()``. This is useful for setting default values that are of mutable types.
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

        # `default_value` and `default_factory` are mutually exclusive
        if default_value is not self.missing and default_factory is not self.missing:
            self._raise_init_type_error('must not be both present',
                                        default_value=default_value,
                                        default_factory=default_factory)

        # `default_factory` must be a callable if provided
        if default_factory is not self.missing and not callable(default_factory):
            self._raise_init_type_error('must be a callable (if present)', default_factory=default_factory)

        # Create a checker from `*args`
        self.checker = Checker.from_checker_likes(args)

        # Set the default factory function
        if default_factory is not self.missing:
            self.default_factory = default_factory
        elif default_value is not self.missing:
            self.default_factory = lambda: default_value
        else:
            self.default_factory = lambda: sentinel

        self.sentinel = sentinel

    def check(self, name, value):
        passed, value = super().check(name, value)
        if not passed:
            return False, value

        if value is self.sentinel:
            return True, self.default_factory()

        result = self.checker.check(name, value)

        if isinstance(result, Wrapper):
            return result
        else:
            passed, value_ = result
            if passed:
                return True, value_
            else:
                return False, self._make_check_error(type(value_), name, value)

    def expected(self):
        return super().expected() + ['missing or'] + self.checker.expected()
