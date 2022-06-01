"""
PathLike
========

This module contains checkers for arguments that represent filesystem paths.
"""
import re
from pathlib import Path

from .utils import join
from .core import Typed


class PathLike(Typed):
    """
    Check if ``x`` is of a path-like type (``str`` or ``pathlib.Path``).

    Additional checks and conversions can be performed by changing some of the default parameters.

    :param is_dir: *bool* – If ``True``, ``x`` must point to an existing directory.
    :param is_file: *bool* – If ``True``, ``x`` must point to an existing file.
    :param suffix: *Optional[str]* – ``x`` must have this suffix (wildcards and regex are not supported).
    :param suffixes: *Optional[List[str]]* – ``x`` must have these suffixes (wildcards and regex are not supported).
       If both ``suffix`` and ``suffixes`` are provided, then, ``x``'s suffix(es) must match at least one of them.
    :param ignore_suffix_case: *bool* – Whether or not the suffix's case should be ignored. Only relevant if
        ``suffix`` or ``suffixes`` are provided.
    :param as_str: *bool* – If ``True``, ``x`` will be converted to ``str`` before it is returned.
    :param as_path: *bool* – If ``True``, ``x`` will be converted to ``pathlib.Path`` before it is returned.
    """
    def __init__(self, is_dir=False, is_file=False, suffix=None, suffixes=None, ignore_suffix_case=True, as_str=False,
                 as_path=False, **kwargs):
        super().__init__(str, Path, **kwargs)

        # Check and set boolean attributes
        self.is_dir = self._validate_bool('is_dir', is_dir)
        self.is_file = self._validate_bool('is_file', is_file)
        self.as_str = self._validate_bool('as_str', as_str)
        self.as_path = self._validate_bool('as_path', as_path)

        # is_dir and is_file are mutually exclusive
        if self.is_dir and self.is_file:
            self._raise_init_value_error('must not be both True', is_dir=is_dir, is_file=is_file)

        # as_str and as_path are mutually exclusive
        if self.as_str and self.as_path:
            self._raise_init_value_error('must not be both True', as_str=as_str, as_path=as_path)

        self.suffix = _Suffix(suffix, suffixes, ignore_suffix_case, parent=self)

    def check(self, name, value):
        passed, value = super().check(name, value)
        if not passed:
            return False, value

        path = Path(value)

        # Check if directory
        if self.is_dir and not path.is_dir():
            return False, self._make_check_error(ValueError, name, value)

        # Check if file
        if self.is_file and not path.is_file():
            return False, self._make_check_error(ValueError, name, value)

        # Check suffix(es)
        passed = self.suffix(name, path)
        if not passed:
            return False, self._make_check_error(ValueError, name, value)

        # Return possibly converted value
        if self.as_path:
            return True, path
        elif self.as_str:
            return True, str(value)
        else:
            return True, value

    def expected(self):
        existing = self.is_dir * 'pointing to an existing directory' + self.is_file * 'pointing to an existing file'
        suffixes = self.suffix.expected_str()
        s = join(', ', [existing, suffixes], on_empty='drop')

        return super().expected() + [s]

    def _validate_bool(self, name, value):
        if not isinstance(value, bool):
            self._raise_init_type_error('must be a bool', **{name: value})

        return value


class ExistingDir(PathLike):
    """
    Same as :class:`.PathLike`, plus, ``x`` must point to an existing directory.

    :meta skip-extend-docstring:
    """
    def __init__(self, *args, **kwargs):
        self._assert_not_in_kwargs('is_dir', **kwargs)
        super().__init__(*args, is_dir=True, **kwargs)


class ExistingFile(PathLike):
    """
    Same as :class:`.PathLike`, plus, ``x`` must point to an existing file.

    :meta skip-extend-docstring:
    """
    def __init__(self, *args, **kwargs):
        self._assert_not_in_kwargs('is_file', **kwargs)
        super().__init__(*args, is_file=True, **kwargs)


class _Suffix:
    def __init__(self, suffix, suffixes, ignore_case, *, parent):
        # ignore_case must be a bool
        if not isinstance(ignore_case, bool):
            parent._raise_init_type_error('must be a bool', ignore_case=ignore_case)

        self.suffix = suffix
        self.suffixes = suffixes
        self.ignore_case = ignore_case

        # Create indicators for whether suffix / suffixes should be checked
        self.suffix_is_provided = self.suffix is not None
        self.suffixes_is_provided = self.suffixes is not None

        # suffix must be None or a string starting with a "."
        if self.suffix_is_provided:
            self._validate_suffix(parent, 'suffix', suffix)

        # suffixes must be None or a list of strings starting with a "."
        if self.suffixes_is_provided:
            if not isinstance(suffixes, list):
                parent._raise_init_type_error('must be a list of strings (if present)', suffixes=suffixes)

            for i, sfx in enumerate(suffixes):
                self._validate_suffix(parent, f'suffixes[{i}]', sfx)

        # Suffixes list of strings is converted to a plain string for convenience
        if self.suffixes_is_provided:
            self.suffixes = ''.join(self.suffixes)

        # If ignoring case, convert suffix and suffixes to lower case
        if self.ignore_case:
            if self.suffix_is_provided:
                self.suffix = self.suffix.lower()
            if self.suffixes_is_provided:
                self.suffixes = self.suffixes.lower()

    def __call__(self, name, value):
        passed = []

        if self.suffix_is_provided:
            passed.append(self._check_suffix(actual=value.suffix, expected=self.suffix))

        if self.suffixes_is_provided:
            passed.append(self._check_suffix(actual=''.join(value.suffixes), expected=self.suffixes))

        # The suffix(es) check passes if no suffix(es) were provided or at least one of them passes
        return not passed or True in passed

    def expected_str(self):
        suffixes = self.suffix_is_provided * [self.suffix] + self.suffixes_is_provided * [self.suffixes]
        suffixes = ' or '.join(suffixes)
        parts = ['with suffix', suffixes, f'(case {"in" if self.ignore_case else ""}sensitive)']
        suffixes = join(' ', parts, on_empty='abort')

        return suffixes

    def _validate_suffix(self, parent, name, value):
        if not isinstance(value, str):
            parent._raise_init_type_error('must be a string (if present)', **{name: value})

        if re.fullmatch(r'(|\.[^\.]+)', value) is None:
            parent._raise_init_value_error('must start with a dot (if present)', **{name: value})

    def _check_suffix(self, actual, expected):
        if self.ignore_case:
            actual = actual.lower()

        return expected == actual
