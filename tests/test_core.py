from argscheck import Checker, Typed, Ordered, Sized, One, Optional

from tests.argscheck_test_case import TestCaseArgscheck


class MockClass:
    pass


class TestTyped(TestCaseArgscheck):
    def test_init(self):
        # Good arguments
        Typed(MockClass)
        Typed(int)
        Typed(type(None))
        Typed(Checker)
        Typed(type)
        Typed(int, float)
        Typed(int, bool, list, dict, str, MockClass)

        # Bad arguments
        self.assertRaises(TypeError, Typed)
        self.assertRaises(TypeError, Typed, None)
        self.assertRaises(TypeError, Typed, 1)
        self.assertRaises(TypeError, Typed, tuple())
        self.assertRaises(TypeError, Typed, MockClass())

    def test_check(self):
        self.checker = Typed(float)
        self.assertOutputIsInput(1e5)
        self.assertOutputIsInput(float('nan'))
        self.assertOutputIsInput(float('inf'))
        self.assertOutputIsInput(float('-inf'))
        self.assertRaisesOnCheck(TypeError, 1)

        self.checker = Typed(int)
        self.assertOutputIsInput(True)
        self.assertOutputIsInput(-1234)
        self.assertRaisesOnCheck(TypeError, 1e5)

        self.checker = Typed(list)
        self.assertOutputIsInput(['', {}, [], ()])
        self.assertOutputIsInput([])
        self.assertRaisesOnCheck(TypeError, {})
        self.assertRaisesOnCheck(TypeError, ())

        self.checker = Typed(Typed)
        self.assertOutputIsInput(self.checker)
        self.assertRaisesOnCheck(TypeError, Checker())

        self.checker = Typed(int, float)
        self.assertOutputIsInput(-12)
        self.assertOutputIsInput(1.234)

        self.checker = Typed(bool)
        self.assertRaisesOnCheck(TypeError, 1)

        self.checker = Typed(str)
        self.assertOutputIsInput('')
        self.assertOutputIsInput('abcd')
        self.assertRaisesOnCheck(TypeError, 0x1234)


class TestOrdered(TestCaseArgscheck):
    def test_init(self):
        # Good arguments
        Ordered()
        Ordered(le=1.0)
        Ordered(gt=-4)
        Ordered(ge=-4, lt=10.4)
        Ordered(ge=-99.9, lt=-10, ne=-50)
        Ordered(eq=3)

        # Bad arguments
        self.assertRaises(TypeError, Ordered, le='abcd')
        self.assertRaises(TypeError, Ordered, eq=3, lt=1)
        self.assertRaises(ValueError, Ordered, ge=4, le=3)

    def test_check(self):
        self.checker = Ordered()
        self.assertOutputIsInput(1e5)
        self.assertOutputIsInput('')
        self.assertOutputIsInput(float('nan'))

        self.checker = Ordered(gt=3.0, ne=3.1, le=3.14)
        self.assertOutputIsInput(3.14)
        self.assertOutputIsInput(3.11)
        self.assertRaisesOnCheck(ValueError, 3.1)
        self.assertRaisesOnCheck(ValueError, 3.0)
        self.assertRaisesOnCheck(ValueError, float('inf'))
        self.assertRaisesOnCheck(ValueError, float('-inf'))
        self.assertRaisesOnCheck(ValueError, float('nan'))

        self.checker = Ordered(ne=0)
        self.assertOutputIsInput(1)
        self.assertOutputIsInput(None)
        self.assertRaisesOnCheck(ValueError, 0.0)

        self.checker = Ordered(eq=-19)
        self.assertOutputIsInput(-19.0)
        self.assertRaisesOnCheck(ValueError, -19.0001)

        self.checker = Ordered(ge=-19)
        self.assertOutputIsInput(-19.0)
        self.assertOutputIsInput(-18.9)
        self.assertRaisesOnCheck(ValueError, -19.1)

        self.checker = Ordered(gt=float('-inf'), lt=float('inf'))
        self.assertOutputIsInput(0)
        self.assertOutputIsInput(2**10)
        self.assertOutputIsInput(-2 ** 10)


class TestSized(TestCaseArgscheck):
    def test_init(self):
        # Good arguments
        Sized()
        Sized(len_eq=5)
        Sized(len_ge=4)
        Sized(len_ge=0, len_le=10)

        # Bad arguments
        self.assertRaises(TypeError, Sized, len_eq='asd')
        self.assertRaises(TypeError, Sized, len_eq=1, len_ne=1)

    def test_check(self):
        self.checker = Sized()
        self.assertOutputIsInput([1, 2, 3])
        self.assertRaisesOnCheck(TypeError, 1)

        self.checker = Sized(len_ge=0)
        self.assertOutputIsInput([1, 2, 3])

        self.checker = Sized(len_ge=0, len_le=3)
        self.assertOutputIsInput([1, 2, 3])
        self.assertRaisesOnCheck(ValueError, [1, 2, 3, 4])

        self.checker = Sized(len_eq=0)
        self.assertOutputIsInput({})
        self.assertRaisesOnCheck(ValueError, [1])

        self.checker = Sized(len_ne=2)
        self.assertOutputIsInput({})
        self.assertOutputIsInput({1, 2, 3})
        self.assertRaisesOnCheck(TypeError, True)
        self.assertRaisesOnCheck(ValueError, dict(a=1, b=2))

        self.checker = Sized(len_lt=3)
        self.assertOutputIsInput({1, 2})
        self.assertRaisesOnCheck(ValueError, {1, 'a', 3.14})


class TestOne(TestCaseArgscheck):
    def test_init(self):
        # Good arguments
        One(int, float)
        One(Ordered(), Sized())
        One(Ordered, Sized)
        One(Ordered, int)

        # Bad arguments
        self.assertRaises(TypeError, One)
        self.assertRaises(TypeError, One, int)
        self.assertRaises(TypeError, One, int, None)
        self.assertRaises(TypeError, One, str, 2)

    def test_check(self):
        self.checker = One(int, str)
        self.assertOutputIsInput('abcd')
        self.assertOutputIsInput(1234)
        self.assertOutputIsInput(True)
        self.assertRaisesOnCheck(ValueError, 1.1)

        self.checker = One(int, bool)
        self.assertOutputIsInput(int(1e5))
        self.assertRaisesOnCheck(ValueError, True)

        self.checker = One(float, str, bool, Sized(len_eq=2))
        self.assertOutputIsInput(1.234)
        self.assertOutputIsInput('abcd')
        self.assertOutputIsInput({1, 'a'})
        self.assertRaisesOnCheck(ValueError, [1, 2, 3])
        self.assertRaisesOnCheck(ValueError, 1)

        self.checker = One(Sized, list)
        self.assertRaisesOnCheck(ValueError, [])


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
        self.assertRaisesOnCheck(ValueError, 'abcd')

        sentinel = object()
        self.checker = Optional(int, sentinel=sentinel)
        self.assertOutputIsInput(1234)
        self.assertOutputIsInput(sentinel)
        self.assertRaisesOnCheck(ValueError, None)

        default_value = 1234567
        self.checker = Optional(int, list, default_value=default_value)
        self.assertOutputIsInput(111)
        self.assertOutputIsInput([1, 1, 1])
        self.assertOutputIs(None, default_value)
        self.assertRaisesOnCheck(ValueError, 'abcd')

        self.checker = Optional(int, list, default_factory=list)
        self.assertOutputIsInput(111)
        self.assertOutputIsInput([1, 1, 1])
        self.assertOutputEqual(None, [])
        self.assertRaisesOnCheck(ValueError, 'abcd')

        sentinel = object()
        self.checker = Optional(int, list, default_factory=list, sentinel=sentinel)
        self.assertOutputIsInput(1234)
        self.assertOutputIsInput([1, 1, 1])
        self.assertOutputEqual(sentinel, [])
        self.assertRaisesOnCheck(ValueError, None)
