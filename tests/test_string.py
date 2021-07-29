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
        # Good arguments
        self.assertOutputIsInput(String(), 'abcd')
        self.assertOutputIsInput(String('.bcd'), 'abcd')
        self.assertOutputIsInput(String('.bcd'), 'abcde')
        self.assertOutputIsInput(String('.bcd'), '1bcd')
        self.assertOutputIsInput(String('.bcd', method='search'), '111abcde')
        self.assertOutputIsInput(String('.bcd', method='search'), 'abcde')
        self.assertOutputIsInput(String('.bcd', flags=re.IGNORECASE), 'abcde')
        self.assertOutputIsInput(String('.bcd', flags=re.IGNORECASE), 'ABCDE')

        # Bad arguments
        self.assertRaises(TypeError, String(), 1234)
        self.assertRaises(ValueError, String('.bcd').check, '111abcde')
        self.assertRaises(ValueError, String('.bcd').check, 'ABCDE')
        self.assertRaises(ValueError, String('.bcd', method='fullmatch').check, 'abcde')
        self.assertRaises(ValueError, String('.bcd', method='fullmatch').check, 'ac')
