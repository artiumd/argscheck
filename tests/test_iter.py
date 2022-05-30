from argscheck import Iterator, Iterable, Optional, check_args

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
        Iterable(Optional(int, default_value=66)).check([1, 2, None, 3])

        # Bad arguments
        self.assertRaises(TypeError, Iterable, None)
        self.assertRaises(TypeError, Iterable, MockIterator('ret'))

    def test_check(self):
        values = ([], [], [])
        iter_checker = Iterable(list).check(MockIterable(values))

        i = 0
        for item, value in zip(iter_checker, values):
            self.assertIs(item, value)
            i += 1
        self.assertEqual(i, len(values))

        values = [1, 2, None, 3]
        checker = Iterable(Optional(int, default_value=66))

        ret = list(checker.check(values))
        self.assertEqual(ret, [1, 2, 66, 3])

        iter_checker = Iterable(int).check(MockIterable('ret'))
        self.assertRaises(TypeError, list, iter_checker)

        checker = Iterable(str, bool)
        iterable = checker.check(['a', True, 1.1])

        iterator = iter(iterable)
        self.assertEqual(next(iterator), 'a')
        self.assertEqual(next(iterator), True)
        with self.assertRaises(Exception):
            next(iterator)

        @check_args
        def fn(x: Iterable(int)):
            return list(x)

        fn(MockIterable((1, 2, 3)))


class TestIterator(TestCaseArgscheck):
    def test_init(self):
        Iterator(str).check(MockIterator('ret'))

        self.assertRaises(TypeError, Iterator, None)
        self.assertRaises(TypeError, Iterator, None)

    def test_check(self):
        values = ([], [], [])
        iterator = MockIterator(values)
        checker = Iterator(list)
        checker.check(iterator)

        for value in values:
            ret = next(checker)
            self.assertIs(value, ret)

        with self.assertRaises(StopIteration):
            next(checker)

        # Each item must be an str or bool instance
        checker = Iterator(str, bool)
        iterator = checker.check(iter(['a', True, 1.1]))

        self.assertEqual(next(iterator), 'a')
        self.assertEqual(next(iterator), True)
        with self.assertRaises(Exception):
            next(iterator)

        @check_args
        def fn(x: Iterator(int)):
            yield from x

        fn(MockIterable([1, 2, 3]))
