from argscheck import Checker, Typed, Sized, One, Optional, Comparable

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
        self.assertOutputIsInput(0.0)
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
        self.assertOutputIsInput(False)
        self.assertRaisesOnCheck(TypeError, 1)  # 1 is not a bool
        self.assertRaisesOnCheck(TypeError, None)

        self.checker = Typed(str)
        self.assertOutputIsInput('')
        self.assertOutputIsInput('abcd')
        self.assertRaisesOnCheck(TypeError, 0x1234)


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


class TestOne(TestCaseArgscheck):
    def test_init(self):
        # Good arguments
        One(int, float)
        One(Comparable(), Sized())
        One(Comparable, Sized)
        One(Comparable, int)

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
        self.assertRaisesOnCheck(Exception, 1.1)

        self.checker = One(int, bool)
        self.assertOutputIsInput(int(1e5))
        self.assertRaisesOnCheck(Exception, True)  # True is both an int and a bool

        self.checker = One(float, str, bool, Sized(len_eq=2))
        self.assertOutputIsInput(1.234)
        self.assertOutputIsInput('abcd')
        self.assertOutputIsInput({1, 'a'})
        self.assertRaisesOnCheck(Exception, [1, 2, 3])
        self.assertRaisesOnCheck(Exception, 1)

        self.checker = One(Sized, list)
        self.assertRaisesOnCheck(Exception, [])  # [] is both a list and has a length


class TestComparable(TestCaseArgscheck):
    def test_init(self):
        # Good arguments
        Comparable()
        Comparable(le=1.0)
        Comparable(gt=-4)
        Comparable(ge=-4, lt=10.4)
        Comparable(ge=-99.9, lt=-10, ne=-50)
        Comparable(eq=3)

        # Bad arguments
        self.assertRaises(TypeError, Comparable, eq=3, lt=1)
        self.assertRaises(ValueError, Comparable, ge=4, le=3)

    def test_check(self):
        self.checker = Comparable()
        self.assertOutputIsInput(1e5)
        self.assertOutputIsInput('')
        self.assertOutputIsInput(float('nan'))

        self.checker = Comparable(gt=3.0, ne=3.1, le=3.14)
        self.assertOutputIsInput(3.14)
        self.assertOutputIsInput(3.11)
        self.assertRaisesOnCheck(ValueError, 3.1)
        self.assertRaisesOnCheck(ValueError, 3.0)
        self.assertRaisesOnCheck(ValueError, float('inf'))
        self.assertRaisesOnCheck(ValueError, float('-inf'))
        self.assertRaisesOnCheck(ValueError, float('nan'))

        self.checker = Comparable(ne=0)
        self.assertOutputIsInput(1)
        self.assertOutputIsInput(None)
        self.assertRaisesOnCheck(ValueError, 0.0)

        self.checker = Comparable(eq=-19)
        self.assertOutputIsInput(-19.0)
        self.assertRaisesOnCheck(ValueError, -19.0001)

        self.checker = Comparable(ge=-19)
        self.assertOutputIsInput(-19.0)
        self.assertOutputIsInput(-18.9)
        self.assertRaisesOnCheck(ValueError, -19.1)

        self.checker = Comparable(gt=float('-inf'), lt=float('inf'))
        self.assertOutputIsInput(0)
        self.assertOutputIsInput(2**10)
        self.assertOutputIsInput(-2 ** 10)

        self.checker = Comparable(le='abcd')
        self.assertRaisesOnCheck(TypeError, -19.0001)

        self.checker = Comparable(ne='abcd')
        self.assertOutputIsInput(100)
        self.assertOutputIsInput('abcde')

        self.checker = Comparable(lt={'a', 'b'})
        self.assertOutputIsInput(set())
        self.assertOutputIsInput({'a'})
        self.assertRaisesOnCheck(ValueError, {'a', 'b'})
        self.assertRaisesOnCheck(TypeError, 'a')

        self.checker = Comparable(gt=0.0, le=10.0)
        self.assertOutputIsInput(1)
        self.assertOutputIsInput(10.0)
        self.assertRaisesOnCheck(ValueError, 0)
        self.assertRaisesOnCheck(ValueError, 10.01)
        self.assertRaisesOnCheck(TypeError, 'a')