from argscheck import Optional, Collection, Set

from tests.argscheck_test_case import TestCaseArgscheck


class MockCollection:
    def __init__(self, items):
        self.items = list(items)

    def __iter__(self):
        return iter(self.items)

    def __len__(self):
        return len(self.items)

    def __eq__(self, other):
        return set(self.items) == set(other.items)


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
