import unittest

from argscheck import Checker


class TestCaseArgscheck(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._checker = None

    @property
    def checker(self):
        if self._checker is None:
            raise ValueError(f'checker property of {self!r} has not been set yet.')

        return self._checker

    @checker.setter
    def checker(self, value):
        if value is not None and not isinstance(value, Checker):
            raise TypeError(f'checker property of {self!r} must be None or a checker instance. Got {value!r}.')

        self._checker = value

    def assertOutputIsInput(self, *args):
        # Unpack arguments
        if len(args) == 2:
            checker, value = args
            self.checker = None
        elif len(args) == 1:
            checker, value = self.checker, args[0]
        else:
            raise TypeError(f'{self!r}.assertOutputIsInput() expects one or two arguments, got {len(args)} instead.')

        ret = checker.check(value)
        self.assertIs(ret, value)
