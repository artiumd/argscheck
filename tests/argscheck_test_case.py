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

    def assertOutputIsInput(self, value):
        ret = self.checker.check(value)
        self.assertIs(ret, value)

    def assertOutputIs(self, value, exp_output):
        ret = self.checker.check(value)
        self.assertIs(ret, exp_output)

    def assertOutputEqual(self, value, exp_output):
        ret = self.checker.check(value)
        self.assertEqual(ret, exp_output)

    def assertRaisesOnCheck(self, expected_exception, *args, **kwargs):
        return self.assertRaises(expected_exception, self.checker.check, *args, **kwargs)
