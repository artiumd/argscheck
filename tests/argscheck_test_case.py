import unittest
from functools import partial

from argscheck import check, Checker


class TestCaseArgscheck(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._checker = None

    def get_checker(self):
        if self._checker is None:
            raise ValueError(f'checker property of {self!r} has not been set yet.')

        return self._checker

    def set_checker(self, value):
        if value is not None and not isinstance(value, Checker):
            raise TypeError(f'checker property of {self!r} must be None or a checker instance. Got {value!r}.')

        self._checker = value

    checker = property(get_checker, set_checker)

    def assertOutputIsInput(self, value):
        ret = check(self.checker, value)
        self.assertIs(ret, value)

    def assertOutputEqualsInput(self, value):
        ret = check(self.checker, value)
        self.assertEqual(ret, value)

    def assertOutputIs(self, value, exp_output):
        ret = check(self.checker, value)
        self.assertIs(ret, exp_output)

    def assertOutputEquals(self, value, exp_output):
        ret = check(self.checker, value)
        self.assertEqual(ret, exp_output)

    def assertRaisesOnCheck(self, expected_exception, *args, **kwargs):
        return self.assertRaises(expected_exception, partial(check, self.checker), *args, **kwargs)
