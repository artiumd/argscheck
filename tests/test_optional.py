from argscheck import Optional

from tests.argscheck_test_case import TestCaseArgscheck


class TestOptional(TestCaseArgscheck):
    def test_init(self):
        # Good arguments
        Optional(int)
        Optional(str, dict)
        Optional(str, dict, default_value=1)
        Optional(str, dict, default_factory=list)
        Optional(str, dict, sentinel=object())

        # Bad arguments
        self.assertRaises(TypeError, Optional)
        self.assertRaises(TypeError, Optional, 1)
        self.assertRaises(TypeError, Optional, None)
        self.assertRaises(TypeError, Optional, None, str)
        self.assertRaises(TypeError, Optional, int, default_value=1, default_factory=int)
        self.assertRaises(TypeError, Optional, int, default_factory=1)

    def test_check(self):
        self.checker = Optional(int)
        self.assertOutputIsInput(1234)
        self.assertOutputIsInput(None)
        self.assertRaisesOnCheck(TypeError, 'abcd')

        sentinel = object()
        self.checker = Optional(int, sentinel=sentinel)
        self.assertOutputIsInput(1234)
        self.assertOutputIsInput(sentinel)
        self.assertRaisesOnCheck(TypeError, None)

        default_value = 1234567
        self.checker = Optional(int, list, default_value=default_value)
        self.assertOutputIsInput(111)
        self.assertOutputIsInput([1, 1, 1])
        self.assertOutputIs(None, default_value)
        self.assertRaisesOnCheck(Exception, 'abcd')

        self.checker = Optional(int, list, default_factory=list)
        self.assertOutputIsInput(111)
        self.assertOutputIsInput([1, 1, 1])
        self.assertOutputEquals(None, [])
        self.assertRaisesOnCheck(Exception, 'abcd')

        sentinel = object()
        self.checker = Optional(int, list, default_factory=list, sentinel=sentinel)
        self.assertOutputIsInput(1234)
        self.assertOutputIsInput([1, 1, 1])
        self.assertOutputEquals(sentinel, [])
        self.assertRaisesOnCheck(Exception, None)
