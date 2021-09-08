from pathlib import Path

from .core import Typed, Optional
from .sequence import List
from .string import String


_bool_typed = Typed(bool)
_suffix = String(r'(|\.[^\.]+)')  # Empty string or a dot followed by one or more "non-dot" characters
_optional_suffix = Optional(_suffix)
_optional_suffix_list = Optional(List(_suffix))


class PathLike(Typed):
    def __init__(self, is_dir=False, is_file=False, suffix=None, suffixes=None, ignore_suffix_case=True, as_str=False,
                 as_path=False, **kwargs):
        super().__init__(str, Path, **kwargs)

        # Check and set boolean attributes
        self.is_dir = _bool_typed.check(is_dir=is_dir)
        self.is_file = _bool_typed.check(is_file=is_file)
        self.ignore_suffix_case = _bool_typed.check(ignore_suffix_case=ignore_suffix_case)
        self.as_str = _bool_typed.check(as_str=as_str)
        self.as_path = _bool_typed.check(as_path=as_path)

        # is_dir and is_file are mutually exclusive
        if self.is_dir and self.is_file:
            raise ValueError('PathLike() got both is_dir=True and is_file=True')

        # as_str and as_path are mutually exclusive
        if self.as_str and self.as_path:
            raise ValueError('PathLike() got both as_str=True and as_path=True')

        # If a suffix is provided, it must be a string.
        self.suffix = _optional_suffix.check(suffix=suffix)

        # If a suffixes is provided, it must be a list of strings.
        self.suffixes = _optional_suffix_list.check(suffixes=suffixes)

        if self.suffixes is not None:
            self.suffixes = ''.join(self.suffixes)

        if self.ignore_suffix_case:
            if self.suffix is not None:
                self.suffix = self.suffix.lower()
            if self.suffixes is not None:
                self.suffixes = self.suffixes.lower()

        self.min_count = max(self.suffix is not None, self.suffixes is not None)

    def __call__(self, name, value):
        passed, value = super().__call__(name, value)
        if not passed:
            return False, value

        path = Path(value)

        if self.is_dir and not path.is_dir():
            return False, ValueError(f'Expected {name} = {path} to be an existing directory.')

        if self.is_file and not path.is_file():
            return False, ValueError(f'Expected {name} = {path} to be an existing file.')

        fail_count = 0

        # Check suffix
        if self.suffix is not None:
            suffix = path.suffix

            if self.ignore_suffix_case:
                suffix = suffix.lower()

            if self.suffix != suffix:
                fail_count += 1

        # Check suffixes
        if self.suffixes is not None:
            suffixes = ''.join(path.suffixes)

            if self.ignore_suffix_case:
                suffixes = suffixes.lower()

            if self.suffixes != suffixes:
                fail_count += 1

        # Return error if both suffix and suffixes do not match
        if fail_count > self.min_count:
            expected_suffixes = (self.suffix is not None) * [f'suffix {self.suffix}'] + \
                                (self.suffixes is not None) * [f'suffixes {"".join(self.suffixes)}']
            expected_suffixes = ' or '.join(expected_suffixes)

            return False, ValueError(f'Expected {name} = {path} to to have {expected_suffixes}')

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
