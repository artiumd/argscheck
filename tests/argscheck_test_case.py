import unittest

from argscheck import Checker


class ArgscheckTestCase(unittest.TestCase):
    def __init__(self):
        super().__init__()
        self._checker = None

    @property
    def checker(self):
        if self._checker is None:
            raise ValueError(f'checker property of {self!r} has not been set yet.')

        return self._checker

    @checker.setter
    def checker(self, value):
        if not isinstance(value, Checker):
            raise TypeError(f'checker property of {self!r} must be a checker instance. Got {value!r}')

        self._checker = value
