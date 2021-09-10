from pathlib import Path

from .core import Typed, Optional
from .sequence import List
from .string import String


_bool_typed = Typed(bool)
_suffix = String(r'(|\.[^\.]+)')  # Empty string or a dot followed by one or more "non-dot" characters
_optional_suffix = Optional(_suffix)
_optional_suffix_list = Optional(List(_suffix))


class _Suffix:
    def __init__(self, suffix, suffixes, ignore_case):
        # Check and set arguments
        self.ignore_case = _bool_typed.check(ignore_suffix_case=ignore_case)
        self.suffix = _optional_suffix.check(suffix=suffix)
        self.suffixes = _optional_suffix_list.check(suffixes=suffixes)

        # Create indicators for whether suffix / suffixes should be checked
        self.suffix_is_provided = self.suffix is not None
        self.suffixes_is_provided = self.suffixes is not None

        # Suffixes list of strings is converted to a plain string for convenience
        if self.suffixes_is_provided:
            self.suffixes = ''.join(self.suffixes)

        # If ignoring case, convert suffix and suffixes to lower case
        if self.ignore_case:
            if self.suffix_is_provided:
                self.suffix = self.suffix.lower()
            if self.suffixes_is_provided:
                self.suffixes = self.suffixes.lower()

        # If both suffix and suffixes are provided, it is sufficient that only one of them passes
        self.max_fail_count = int(self.suffix_is_provided or self.suffixes_is_provided)

    def _check_suffix(self, actual, expected):
        if self.ignore_case:
            actual = actual.lower()

        return expected != actual

    def __call__(self, name, value):
        # Check suffix
        suffix_failed = self.suffix_is_provided and self._check_suffix(actual=value.suffix,
                                                                       expected=self.suffix)
        # Check suffixes
        suffixes_failed = self.suffixes_is_provided and self._check_suffix(actual=''.join(value.suffixes),
                                                                           expected=self.suffixes)

        # Return error if both suffix and suffixes do not match
        if suffix_failed + suffixes_failed > self.max_fail_count:
            expected_suffixes = self.suffix_is_provided * [f'suffix {self.suffix}'] + \
                                self.suffixes_is_provided * [f'suffixes {self.suffixes}']
            expected_suffixes = ' or '.join(expected_suffixes)

            return False, ValueError(f'Expected {name} = {value} to to have {expected_suffixes}')
        else:
            return True, value


class PathLike(Typed):
    def __init__(self, is_dir=False, is_file=False, suffix=None, suffixes=None, ignore_suffix_case=True, as_str=False,
                 as_path=False, **kwargs):
        super().__init__(str, Path, **kwargs)

        # Check and set boolean attributes
        self.is_dir = _bool_typed.check(is_dir=is_dir)
        self.is_file = _bool_typed.check(is_file=is_file)
        self.as_str = _bool_typed.check(as_str=as_str)
        self.as_path = _bool_typed.check(as_path=as_path)

        # is_dir and is_file are mutually exclusive
        if self.is_dir and self.is_file:
            raise ValueError('PathLike() got both is_dir=True and is_file=True')

        # as_str and as_path are mutually exclusive
        if self.as_str and self.as_path:
            raise ValueError('PathLike() got both as_str=True and as_path=True')

        self.suffix = _Suffix(suffix, suffixes, ignore_suffix_case)

    def __call__(self, name, value):
        passed, value = super().__call__(name, value)
        if not passed:
            return False, value

        path = Path(value)

        # Check for directory
        if self.is_dir and not path.is_dir():
            return False, ValueError(f'Expected {name} = {path} to be an existing directory.')

        # Check for file
        if self.is_file and not path.is_file():
            return False, ValueError(f'Expected {name} = {path} to be an existing file.')

        # Check suffix(es)
        passed, e = self.suffix(name, path)
        if not passed:
            return False, e

        # Return possibly converted value
        if self.as_path:
            return True, path
        elif self.as_str:
            return True, str(value)
        else:
            return True, value


class ExistingDirectory(PathLike):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, is_dir=True, **kwargs)


class ExistingFile(PathLike):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, is_file=True, **kwargs)


# Aliases
ExistingDir = ExistingDirectory
