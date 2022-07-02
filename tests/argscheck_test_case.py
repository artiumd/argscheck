import unittest
from functools import partial

from argscheck import check


class TestCaseArgscheck(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._checker = None

    def get_checker(self):
        if self._checker is None:
            raise ValueError(f'checker property of {self!r} has not been set yet.')

        return self._checker

    def set_checker(self, value):
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

    def assertItemsFromIter(self, value, exp_behaviours, exp_output, iterable):
        checker = check(self.checker, value)

        if iterable:
            checker = iter(checker)

        for behaviour, expected_value in zip(exp_behaviours, exp_output):
            if behaviour == 'is':
                actual_value = next(checker)
                self.assertIs(actual_value, expected_value)
            elif behaviour == 'equal':
                actual_value = next(checker)
                self.assertEqual(actual_value, expected_value)
            elif behaviour.startswith('raises'):
                expected_exception = eval(behaviour.split(':')[1])

                with self.assertRaises(expected_exception):
                    next(checker)
            else:
                raise ValueError(f'assertItemsFromIterator got unexpected behaviour key: {behaviour}')

        with self.assertRaises(StopIteration):
            next(checker)
