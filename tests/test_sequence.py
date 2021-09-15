from argscheck import Optional, List, Tuple, Sequence

from tests.argscheck_test_case import TestCaseArgscheck


class TestSequence(TestCaseArgscheck):
    def test_check(self):
        self.checker = Sequence(str, len_ge=2)
        self.assertOutputIsInput(('a', 'b'))
        self.assertOutputIsInput(['a', 'b'])
        self.assertRaisesOnCheck(TypeError, {'a', 'b'})
        self.assertRaisesOnCheck(ValueError, ['a'])
        self.assertRaisesOnCheck(TypeError, ['a', 1])


class TestTuple(TestCaseArgscheck):
    def test_init(self):
        # Good arguments
        Tuple(str)
        Tuple(Optional(int), len_ge=2)

        # Bad arguments
        self.assertRaises(TypeError, Tuple, method=1)
        self.assertRaises(TypeError, Tuple, 1234)
        self.assertRaises(TypeError, Tuple, 'abcd', flags=1.1)

    def test_check(self):
        self.checker = Tuple(str)
        self.assertOutputIsInput(())
        self.assertOutputIsInput(('abcd',))
        self.assertOutputIsInput(('abcde', 'abcd'))
        self.assertRaisesOnCheck(TypeError, '111abcde')
        self.assertRaisesOnCheck(TypeError, (1, 2, 3))

        self.checker = Tuple(Optional(int, default_value=66), len_ge=2)
        self.assertOutputIsInput((1, 2))
        self.assertOutputEquals((1, 2, 3, 4, None), (1, 2, 3, 4, 66))
        self.assertRaisesOnCheck(ValueError, (1,))
        self.assertRaisesOnCheck(TypeError, 123)


class TestList(TestCaseArgscheck):
    def test_init(self):
        # Good arguments
        List(str)
        List(Optional(int), len_ge=2)

        # Bad arguments
        self.assertRaises(TypeError, List, method=1)
        self.assertRaises(TypeError, List, 1234)
        self.assertRaises(TypeError, List, 'abcd', flags=1.1)

    def test_check(self):
        self.checker = List(str)
        self.assertOutputIsInput([])
        self.assertOutputIsInput(['abcd'])
        self.assertOutputIsInput(['abcde', 'abcd'])
        self.assertRaisesOnCheck(TypeError, '111abcde')
        self.assertRaisesOnCheck(TypeError, [1, 2, 3])

        self.checker = List(Optional(int, default_value=66), len_ge=2)
        self.assertOutputIsInput([1, 2])
        self.assertOutputEquals([1, 2, 3, 4, None], [1, 2, 3, 4, 66])
        self.assertRaisesOnCheck(ValueError, [1])
        self.assertRaisesOnCheck(TypeError, 123)
