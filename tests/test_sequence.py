from argscheck import Optional, List

from tests.argscheck_test_case import TestCaseArgscheck


class TestList(TestCaseArgscheck):
    def test_init(self):
        # Good arguments
        # List()
        List(str)
        List(Optional(int), len_ge=2)

        # Bad arguments
        self.assertRaises(TypeError, List, method=1)
        self.assertRaises(TypeError, List, 1234)
        self.assertRaises(TypeError, List, 'abcd', flags=1.1)

    def test_check(self):
        # self.checker = List()
        # self.assertOutputEqualsInput([])
        # self.assertRaisesOnCheck(TypeError, 1234)

        self.checker = List(str)
        self.assertOutputEqualsInput([])
        self.assertOutputEqualsInput(['abcd'])
        self.assertOutputEqualsInput(['abcde', 'abcd'])
        self.assertRaisesOnCheck(TypeError, '111abcde')
        self.assertRaisesOnCheck(TypeError, [1, 2, 3])

        self.checker = List(Optional(int, default_value=66), len_ge=2)
        self.assertOutputEqualsInput([1, 2])
        self.assertOutputEqual([1, 2, 3, 4, None], [1, 2, 3, 4, 66])
        self.assertRaisesOnCheck(ValueError, [1])
        self.assertRaisesOnCheck(TypeError, 123)
