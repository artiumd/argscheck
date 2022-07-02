from argscheck import Optional, Collection, Set, Iterator, Iterable

from tests.argscheck_test_case import TestCaseArgscheck
from tests.mocks import MockCollection, MockIterator, MockIterable


class TestCollection(TestCaseArgscheck):
    def test_check(self):
        int_collection = MockCollection([1, 2, 3])
        str_collection = MockCollection(['1', '2', '3'])

        self.checker = Collection(int)
        self.assertOutputEqualsInput(int_collection)
        self.assertRaisesOnCheck(TypeError, str_collection)

        self.checker = Collection(Optional(str, default_value=''))
        self.assertOutputEqualsInput(MockCollection(['1', '2', '3']))
        self.assertOutputEquals(MockCollection(['1', '2', None]), MockCollection(['1', '2', '']))

        self.checker = Collection(float, len_gt=0)
        self.assertOutputEqualsInput({1.2, 3.4})
        self.assertOutputEqualsInput([1.1, 2.2, 3.3])
        self.assertRaisesOnCheck(ValueError, ())
        self.assertRaisesOnCheck(TypeError, 'abcd')


class TestSet(TestCaseArgscheck):
    def test_check(self):
        self.checker = Set(gt={'a'}, len_ge=2)
        self.assertOutputIsInput({'a', 'b'})
        self.assertOutputIsInput({'a', 1, ()})
        self.assertRaisesOnCheck(TypeError, ['a', 'b'])
        self.assertRaisesOnCheck(ValueError, {'a'})
        self.assertRaisesOnCheck(ValueError, {'b', 'c'})

        self.checker = Set[Iterator[str]]
        self.assertRaisesOnCheck(NotImplementedError, {'aa', MockIterator(['a', 'b']), MockIterator(['a', 'b'])})

        self.checker = Set[Iterable[str]]
        self.assertRaisesOnCheck(NotImplementedError, {'aa', MockIterable(['a', 'b']), MockIterable(['a', 'b'])})

        self.checker = Set[str] <= {'one', 'two', 'three'}
        self.assertOutputEqualsInput({'one'})
        self.assertOutputEqualsInput({'one', 'two'})
        self.assertOutputEqualsInput({'one', 'two', 'three'})
        self.assertRaisesOnCheck(ValueError, {'one', 'two', 'three', 'four'})
        self.assertRaisesOnCheck(ValueError, {'four'})
        self.assertRaisesOnCheck(TypeError, {1})

        self.checker = Set(len_ge=2) > {'a'}
        self.assertOutputIsInput({'a', 'b'})
        self.assertOutputIsInput({'a', 1, ()})
        self.assertRaisesOnCheck(TypeError, ['a', 'b'])
        self.assertRaisesOnCheck(ValueError, {'a'})
        self.assertRaisesOnCheck(ValueError, {'b', 'c'})
