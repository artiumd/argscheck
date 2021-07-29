import unittest
import re

from argscheck import String


class TestString(unittest.TestCase):
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
        string = String()
        value = 'abcd'
        ret = string.check(value)
        self.assertIs(ret, value)

        self.assertRaises(TypeError, string.check, 1234)

        string = String('.bcd')

        value = 'abcd'
        ret = string.check(value)
        self.assertIs(ret, value)

        value = 'abcde'
        ret = string.check(value)
        self.assertIs(ret, value)

        self.assertRaises(ValueError, string.check, '111abcde')
        self.assertRaises(ValueError, string.check, 'ABCDE')

        value = '1bcd'
        ret = string.check(value)
        self.assertIs(ret, value)

        string = String('.bcd', method='fullmatch')
        self.assertRaises(ValueError, string.check, 'abcde')
        self.assertRaises(ValueError, string.check, 'ac')

        string = String('.bcd', method='search')

        value = '111abcde'
        ret = string.check(value)
        self.assertIs(ret, value)

        value = 'abcde'
        ret = string.check(value)
        self.assertIs(ret, value)

        string = String('.bcd', flags=re.IGNORECASE)

        value = 'abcde'
        ret = string.check(value)
        self.assertIs(ret, value)

        value = 'ABCDE'
        ret = string.check(value)
        self.assertIs(ret, value)
