from argscheck import Iterator, Iterable, Optional, check_args, check, PositiveNumber

from tests.argscheck_test_case import TestCaseArgscheck
from tests.mocks import MockIterable, MockIterator


class TestIterable(TestCaseArgscheck):
    def test_init(self):
        # Good arguments
        check(Iterable(str), MockIterable('ret'))
        check(Iterable(Optional(int, default_value=66)), [1, 2, None, 3])

        # Bad arguments
        self.assertRaises(TypeError, Iterable, None)
        self.assertRaises(TypeError, Iterable, MockIterator('ret'))

    def test_check(self):

        self.checker = Iterable(list)
        values = ([], [], [])
        behaviours = ['is', 'is', 'is']
        self.assertItemsFromIter(MockIterable(values), behaviours, values, iterable=True)

        self.checker = Iterable(Optional(int, default_value=66))
        values = [1, 2, None, 3]
        expected_value = [1, 2, 66, 3]
        behaviours = ['equal', 'equal', 'equal', 'equal']
        self.assertItemsFromIter(MockIterable(values), behaviours, expected_value, iterable=True)

        self.checker = Iterable(int)
        values = 'ret'
        behaviours = ['raises:TypeError', 'raises:TypeError', 'raises:TypeError']
        self.assertItemsFromIter(MockIterable(values), behaviours, values, iterable=True)

        self.checker = Iterable(str, bool)
        values = ['a', True, 1.1]
        behaviours = ['is', 'is', 'raises:Exception']
        self.assertItemsFromIter(MockIterable(values), behaviours, values, iterable=True)

        @check_args
        def fn(x: Iterable(int)):
            return list(x)

        fn(MockIterable((1, 2, 3)))

        with self.assertRaises(TypeError):
            fn(MockIterable((1, 2, [3])))

        self.checker = Optional[Iterable[int]]
        self.assertOutputEquals(None, None)
        values = [1, 2.1, 3, '', [], -2]
        behaviours = ['is', 'raises:Exception', 'is', 'raises:Exception', 'raises:Exception', 'is']
        self.assertItemsFromIter(MockIterable(values), behaviours, values, iterable=True)

        checker = Iterable(Iterable(int))
        value = [[0, 1, 2], [3, 4, 5]]
        expected_value = 0

        for outer_value in check(checker, value):
            for inner_value in outer_value:
                self.assertEqual(expected_value, inner_value)
                expected_value += 1

        checker = Iterable(Iterable(int))
        value = [['']]

        for outer_value in check(checker, value):
            with self.assertRaises(TypeError):
                for inner_value in outer_value:
                    pass


class TestIterator(TestCaseArgscheck):
    def test_init(self):
        check(Iterator(str), MockIterator('ret'))

        self.assertRaises(TypeError, Iterator, None)
        self.assertRaises(TypeError, Iterator, None)

    def test_check(self):
        self.checker = Iterator(list)
        values = [[], [], []]
        behaviours = ['is', 'is', 'is']
        self.assertItemsFromIter(MockIterator(values), behaviours, values, iterable=False)

        self.checker = Iterator(str, bool)
        values = ['a',  1.1, True]
        behaviours = ['is', 'raises:TypeError', 'is']
        self.assertItemsFromIter(iter(values), behaviours, values, iterable=False)

        @check_args
        def fn(x: Iterator(int)):
            yield from x

        fn(MockIterable([1, 2, 3]))

        self.checker = Optional[Iterator[PositiveNumber, str]]
        self.assertOutputEquals(None, None)
        values = [1, 2.1, 3, '', [], -2]
        behaviours = ['is', 'is', 'is', 'is', 'raises:Exception', 'raises:Exception']
        self.assertItemsFromIter(iter(values), behaviours, values, iterable=False)
