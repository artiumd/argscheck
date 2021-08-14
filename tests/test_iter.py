from argscheck import Iterator, Iterable, Optional

from tests.argscheck_test_case import TestCaseArgscheck


class MockIterable:
    def __init__(self, values):
        self.values = values

    def __iter__(self):
        return MockIterator(self.values)


class MockIterator:
    def __init__(self, values):
        self.values = values
        self.i = 0

    def __next__(self):
        if self.i == len(self.values):
            raise StopIteration
        else:
            ret = self.values[self.i]
            self.i += 1

            return ret


class TestIterable(TestCaseArgscheck):
    def test_init(self):
        # Good arguments
        Iterable(str).check(MockIterable('ret'))
        Iterable(Optional(int, default_value=66)).check(iter([1, 2, None, 3]))

        # Bad arguments
        self.assertRaises(TypeError, Iterable)
        self.assertRaises(TypeError, Iterable, None)

    def test_check(self):
        value = 'ret'
        iter_checker = Iterable(str).check(MockIterable(value))
        i = 0

        for item in iter_checker:
            self.assertIs(item, value[i])
            i += 1

        self.assertEqual(i, len(value))

        checker = Iterable(Optional(int, default_value=66))
        value = [1, 2, None, 3]
        ret = list(checker.check(value))
        self.assertEqual(ret, [1, 2, 66, 3])


class TestIterator(TestCaseArgscheck):
    def test_check(self):
        pass