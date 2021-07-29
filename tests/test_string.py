import unittest
import re

from argscheck import String


class TestString(unittest.TestCase):
    def test_init(self):
        String()
        String(None)
        String('abcd')
        String('abcd', fullmatch=True)
        String('abcd', fullmatch=False)
        String(fullmatch=False)

        with self.assertRaises(TypeError):
            String(fullmatch=1)

        with self.assertRaises(TypeError):
            String(1234)

        with self.assertRaises(TypeError):
            String('abcd', flags=1.1)

    def test_check(self):
        string = String()
        value = 'abcd'
        ret = string.check(value)
        self.assertIs(ret, value)

        with self.assertRaises(TypeError):
            string.check(1234)

        string = String('.bcd')

        value = 'abcd'
        ret = string.check(value)
        self.assertIs(ret, value)

        value = 'abcde'
        ret = string.check(value)
        self.assertIs(ret, value)

        with self.assertRaises(ValueError):
            string.check('ABCDE')

        value = '1bcd'
        ret = string.check(value)
        self.assertIs(ret, value)

        string = String('.bcd', fullmatch=True)
        with self.assertRaises(ValueError):
            string.check('abcde')

        with self.assertRaises(ValueError):
            string.check('ac')

        string = String('.bcd', flags=re.IGNORECASE)

        value = 'abcde'
        ret = string.check(value)
        self.assertIs(ret, value)

        value = 'ABCDE'
        ret = string.check(value)
        self.assertIs(ret, value)
