from argscheck import Checker, Typed, Ordered, Sized, One

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
        Typed(int, bool, list, dict)

        # Bad arguments
        self.assertRaises(TypeError, Typed)
        self.assertRaises(TypeError, Typed, None)
        self.assertRaises(TypeError, Typed, 1)
        self.assertRaises(TypeError, Typed, tuple())

    def test_check(self):
        # Good arguments
        self.assertOutputIsInput(Typed(float), 1e5)
        self.assertOutputIsInput(Typed(int), True)
        self.assertOutputIsInput(Typed(list), [1, 2, 3])
        typed = Typed(Typed)
        self.assertOutputIsInput(typed, typed)
        self.assertOutputIsInput(Typed(int, float), -12)
        self.assertOutputIsInput(Typed(int, float), 1.234)

        # Bad arguments
        self.assertRaises(TypeError, Typed(bool).check, 1)
        self.assertRaises(TypeError, Typed(str).check, 0x1234)


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
        # Good arguments
        self.assertOutputIsInput(Ordered(), 1e5)
        self.assertOutputIsInput(Ordered(gt=3.0, ne=3.1, le=3.14), 3.14)
        self.assertOutputIsInput(Ordered(ne=0), 1)
        self.assertOutputIsInput(Ordered(eq=-19), -19.0)
        self.assertOutputIsInput(Ordered(ge=-19), -19.0)
        self.assertOutputIsInput(Ordered(ge=0.0, le=1.0), 0.5)

        # Bad arguments
        self.assertRaises(ValueError, Ordered(ne=4).check, 4.0)
        self.assertRaises(ValueError, Ordered(eq=4).check, 4.1)
        self.assertRaises(ValueError, Ordered(gt=3).check, 3)
        self.assertRaises(ValueError, Ordered(le=5.5).check, 6)
        self.assertRaises(ValueError, Ordered(ge=0.0, le=1.0).check, 1.1)
        self.assertRaises(TypeError, Ordered(ge=0.0).check, '1.1')


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
        # Good arguments
        self.assertOutputIsInput(Sized(), [1, 2, 3])
        self.assertOutputIsInput(Sized(len_ge=0), [1, 2, 3])
        self.assertOutputIsInput(Sized(len_ge=0, len_le=3), [1, 2, 3])
        self.assertOutputIsInput(Sized(len_eq=0), {})

        # Bad arguments
        self.assertRaises(TypeError, Sized(len_ne=2).check, True)
        self.assertRaises(ValueError, Sized(len_ne=2).check, dict(a=1, b=2))
        self.assertRaises(ValueError, Sized(len_lt=3).check, {1, 'a', 3.14})


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
        # Good arguments
        self.assertOutputIsInput(One(int, str), 'abcd')
        self.assertOutputIsInput(One(int, str), 1234)
        self.assertOutputIsInput(One(int, str), True)
        self.assertOutputIsInput(One(int, bool), int(1e5))
        self.assertOutputIsInput(One(float, str, bool, Sized(len_eq=2)), 1.234)
        self.assertOutputIsInput(One(float, str, bool, Sized(len_eq=2)), 'abcd')
        self.assertOutputIsInput(One(float, str, bool, Sized(len_eq=2)), {1, 'a'})

        # Bad arguments
        self.assertRaises(ValueError, One(int, str).check, 1.1)
        self.assertRaises(ValueError, One(int, bool).check, True)
        self.assertRaises(ValueError, One(float, str, bool, Sized(len_eq=2)).check, [1, 2, 3])
        self.assertRaises(ValueError, One(float, str, bool, Sized(len_eq=2)).check, 1)
        self.assertRaises(ValueError, One(Sized, list).check, [])
