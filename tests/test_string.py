import re

from argscheck import String

from tests.argscheck_test_case import TestCaseArgscheck


class TestString(TestCaseArgscheck):
    def test_init(self):
        # Good arguments
        String()
        String(None)
        String('abcd')
        String('abcd', method='match')
        String('abcd', method='fullmatch')
        String(method='search')

        # Bad arguments
        self.assertRaises(ValueError, String, method=1)
        self.assertRaises(TypeError, String, 1234)
        self.assertRaises(TypeError, String, 'abcd', flags=1.1)

    def test_check(self):
        self.checker = String()
        self.assertOutputIsInput('abcd')
        self.assertRaisesOnCheck(TypeError, 1234)

        self.checker = String('.bcd')
        self.assertOutputIsInput('abcd')
        self.assertOutputIsInput('abcd')
        self.assertOutputIsInput('1bcd')
        self.assertRaisesOnCheck(ValueError, '111abcde')
        self.assertRaisesOnCheck(ValueError, 'abcde')
        self.assertRaisesOnCheck(ValueError, 'ABCDE')

        self.checker = String('.bcd', method='search')
        self.assertOutputIsInput('111abcde')
        self.assertOutputIsInput('abcde')

        self.checker = String('.bcd', flags=re.IGNORECASE)
        self.assertOutputIsInput('abcd')
        self.assertOutputIsInput('ABCD')

        self.checker = String('.bcd', method='fullmatch')
        self.assertRaisesOnCheck(ValueError, 'abcde')
        self.assertRaisesOnCheck(ValueError, 'ac')
