import re

from .core import Typed


class String(Typed):
    def __init__(self, pattern=None, flags=0, fullmatch=False, **kwargs):
        super().__init__(str, **kwargs)

        if not isinstance(fullmatch, bool):
            raise TypeError(f'Argument fullmatch={fullmatch!r} of {self!r}() must be a bool.')

        # Create callable that will return None if value does not match the given pattern
        if pattern is not None:
            re_obj = re.compile(pattern, flags)

            if fullmatch:
                self.matcher = re_obj.fullmatch
            else:
                self.matcher = re_obj.match
        else:
            self.matcher = lambda string: True

        # Save arguments for use in error messages
        self.fullmatch = fullmatch
        self.pattern = pattern

    def __call__(self, name, value):
        passed, value = super().__call__(name, value)
        if not passed:
            return False, value

        # Check if given value match the regex pattern, if no match, return error
        if self.matcher(value) is None:
            fully_ = 'fully ' if self.fullmatch else ''
            return False, ValueError(f'Argument {name}={value} is expected to {fully_}match this regex pattern: '
                                     f'{self.pattern}.')

        return True, value


# Aliases
Str = String
