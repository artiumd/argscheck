class Checker:
    def __repr__(self):
        return type(self).__qualname__

    def __call__(self, name, value):
        return True, value

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


def validate_checker_like(caller, name, value):
    if isinstance(value, tuple) and len(value) == 1:
        return validate_checker_like(caller, name, value[0])
    if isinstance(value, tuple) and len(value) > 1:
        return One(*value)
    if isinstance(value, Checker):
        return value
    if isinstance(value, type) and issubclass(value, Checker):
        return value()
    if isinstance(value, type):
        return Typed(value)

    raise TypeError(f'{caller!r} expects that {name}={value!r} is a checker-like.')


class Typed(Checker):
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


class One(Checker):
    def __init__(self, *checker_likes, **kwargs):
        super().__init__(**kwargs)

        if len(checker_likes) < 2:
            raise TypeError(f'{self!r}() must be called with at least two positional arguments, got {checker_likes!r}.')

        # Validate checker-like positional arguments
        self.checkers = [validate_checker_like(self, f'checker_likes[{i}]', checker_like)
                         for i, checker_like
                         in enumerate(checker_likes)]

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
            return False, ValueError(f'Argument {name}={value!r} is expected to pass exactly one of: {checkers}.')


class Optional(Checker):
    missing = object()

    def __init__(self, *checker_likes, default_value=missing, default_factory=missing, sentinel=None, **kwargs):
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

        self.checker = validate_checker_like(self, 'checker_likes', checker_likes)
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
            return False, ValueError(f'Argument {name}={value!r} is expected to be missing or {self.checker!r}.')
