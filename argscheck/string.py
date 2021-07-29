import re

from .core import Typed


class String(Typed):
    def __init__(self, pattern=None, flags=0, method='match', **kwargs):
        super().__init__(str, **kwargs)

        if method not in {'match', 'fullmatch', 'search'}:
            raise ValueError(f'Argument method={method!r} of {self!r}() must be a "match", "fullmatch" or "search".')

        # Create callable that will return None if value does not match the given pattern
        if pattern is not None:
            re_obj = re.compile(pattern, flags)
            self.matcher = dict(match=re_obj.match, fullmatch=re_obj.fullmatch, search=re_obj.search)[method]
        else:
            self.matcher = lambda string: True

        # Save arguments for use in error messages
        self.method = method
        self.pattern = pattern

    def __call__(self, name, value):
        passed, value = super().__call__(name, value)
        if not passed:
            return False, value

        # Check if given value match the regex pattern, if no match, return error
        if self.matcher(value) is None:
            return False, ValueError(f'Argument {name}={value} is expected to match this regex pattern: '
                                     f'{self.pattern} via the re.{self.method} method.')

        return True, value


# Aliases
Str = String
