"""
String
======
"""
import re

from .core import Typed


class String(Typed):
    """
    Check if argument is a string and optionally, if it matches a particular regex pattern.

    Regex matching is delegated to the builtin ``re`` module.

    :param pattern: *Optional[str]* – Argument must match this regex pattern.
    :param flags: *Optional[re.RegexFlag]* – Flags used for modifying the matching behaviour. Only relevant if
       ``pattern`` is provided.
    :param method: *str* – Name of ``re.Pattern`` method that will be used to match the argument against the regex
        pattern. Must be ``"match"``, ``"fullmatch"`` or ``"search"``. Only relevant if ``pattern`` is provided.

    :Example:

    .. code-block:: python

        from argscheck import String

        # Check if a string ending with ".exe"
        checker = String(".*\.exe$")

        checker.check("app.exe")    # Passes, returns "app.exe"
        checker.check("script.sh")  # Fails, raises ValueError ("script.sh" does not end with ".exe")

    """
    def __init__(self, pattern=None, flags=0, method='match', **kwargs):
        super().__init__(str, **kwargs)

        if method not in {'match', 'fullmatch', 'search'}:
            raise ValueError(f'{self!r}(method={method!r}) must be "match", "fullmatch" or "search".')

        # Create a callable that will return None if value does not match the given pattern
        if pattern is not None:
            re_obj = re.compile(pattern, flags)
            self.re_matcher = getattr(re_obj, method)
        else:
            self.re_matcher = lambda string: True

        # Save arguments for use in error messages
        self.method = method
        self.pattern = pattern

    def __call__(self, name, value):
        passed, value = super().__call__(name, value)
        if not passed:
            return False, value

        # Check if value matches the regex pattern, if not, return an error
        if self.re_matcher(value) is None:
            return False, ValueError(f'Argument {name}={value} is expected to match this regex pattern: '
                                     f'"{self.pattern}" via the re.{self.method} method.')

        return True, value
