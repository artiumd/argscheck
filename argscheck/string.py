"""
String
======
"""
import re

from .core import Typed


class String(Typed):
    """
    Check if ``x`` is a string and optionally, if it matches a particular regex pattern.

    Regex matching is delegated to the builtin ``re`` module.

    :param pattern: *Optional[str]* – ``x`` must match this regex pattern.
    :param flags: *Optional[re.RegexFlag]* – Flags used for modifying the matching behaviour. Only relevant if
       ``pattern`` is provided.
    :param method: *str* – Name of ``re.Pattern`` method that will be used to match ``x`` against the regex pattern.
       Must be ``"match"``, ``"fullmatch"`` or ``"search"``. Only relevant if ``pattern`` is provided.

    :Example:

    .. code-block:: python

        from argscheck import String

        # Check if a string ending with ".exe"
        checker = String(".*\.exe$")

        checker.check("app.exe")    # Passes, returns "app.exe"
        checker.check("script.sh")  # Fails, raises ValueError ("script.sh" does not end with ".exe")

    """
    _allowed_methods = {'match', 'fullmatch', 'search'}

    def __init__(self, pattern=None, flags=0, method='fullmatch', **kwargs):
        super().__init__(str, **kwargs)

        if pattern is not None and not isinstance(pattern, str):
            raise TypeError(f'{self!r}(pattern={pattern!r}) must be None or str.')

        if method not in self._allowed_methods:
            raise ValueError(f'{self!r}(method={method!r}) must be one of {", ".join(self._allowed_methods)}.')

        # Create a callable that will return None if value does not match the given pattern
        if pattern is not None:
            re_obj = re.compile(pattern, flags)
            re_method = getattr(re_obj, method)
            self.re_matcher = lambda string: re_method(string)
        else:
            self.re_matcher = lambda string: True

        # Save arguments for use in error messages
        self.method = method
        self.pattern = pattern

    def expected_str(self):
        if self.pattern is not None:
            s = f'matching the "{self.pattern}" regex pattern via `re.{self.method}()`'
        else:
            s = ''

        return super().expected_str() + [s]

    def __call__(self, name, value):
        passed, value = super().__call__(name, value)
        if not passed:
            return False, value

        # Check if value matches the regex pattern, if not, return an error
        if self.re_matcher(value) is None:
            return False, self._make_error(ValueError, name, value)

        return True, value
