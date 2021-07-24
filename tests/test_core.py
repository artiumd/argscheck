import unittest

from argscheck import Checker, CheckerLike, Typed, Ordered, Sized


class TestCheckerLike(unittest.TestCase):
    def test_check(self):
        # Checker instance
        sized = Sized()
        sized_ret = CheckerLike().check(sized)
        self.assertIs(sized, sized_ret)

        sized_ret = CheckerLike().check((sized,))
        self.assertIs(sized, sized_ret)

        # Checker type
        sized_ret = CheckerLike().check(Sized)
        self.assertIsInstance(sized_ret, Sized)

        sized_ret = CheckerLike().check((Sized,))
        self.assertIsInstance(sized_ret, Sized)

        # Non Checker type
        typed = CheckerLike().check(int)
        self.assertIsInstance(typed, Typed)
        self.assertIs(typed.typ, int)

        typed = CheckerLike().check((int,))
        self.assertIsInstance(typed, Typed)
        self.assertIs(typed.typ, int)

        # Non supported arguments
        with self.assertRaises(TypeError):
            CheckerLike().check(None)
        with self.assertRaises(TypeError):
            CheckerLike().check(1)
        with self.assertRaises(TypeError):
            CheckerLike().check('abcd')
        with self.assertRaises(TypeError):
            CheckerLike().check(list())


class TestTyped(unittest.TestCase):
    def test_init(self):
        # Zero arguments
        with self.assertRaises(TypeError):
            Typed()

        # Two arguments
        with self.assertRaises(TypeError):
            Typed(int, float)

        # Non type argument
        with self.assertRaises(TypeError):
            Typed(None)
        with self.assertRaises(TypeError):
            Typed(1)
        with self.assertRaises(TypeError):
            Typed(tuple())

        # Allowed arguments
        class C:
            pass
        Typed(C)
        Typed(int)
        Typed(type(None))
        Typed(Checker)
        Typed(type)

    def test_check(self):
        value = 1e5
        typed = Typed(float)
        value_ret = typed.check(value)
        self.assertIs(value_ret, value)

        value = True
        typed = Typed(int)
        value_ret = typed.check(value)
        self.assertIs(value_ret, value)

        value = [1, 2, 3]
        typed = Typed(list)
        value_ret = typed.check(value)
        self.assertIs(value_ret, value)

        typed = Typed(Typed)
        value_ret = typed.check(typed)
        self.assertIs(value_ret, typed)

        with self.assertRaises(TypeError):
            Typed(bool).check(1)
        with self.assertRaises(TypeError):
            Typed(str).check(0x1234)


class TestOrdered(unittest.TestCase):
    def test_init(self):
        # Good arguments
        Ordered()
        Ordered(le=1.0)
        Ordered(gt=-4)
        Ordered(ge=-4, lt=10.4)
        Ordered(ge=-99.9, lt=-10, ne=-50)
        Ordered(eq=3)

        # Bad arguments
        with self.assertRaises(TypeError):
            Ordered(le='abcd')
        with self.assertRaises(TypeError):
            Ordered(eq=3, lt=1)
        with self.assertRaises(ValueError):
            Ordered(ge=4, le=3)

    def test_check(self):
        value = 1e5
        ret = Ordered().check(value)
        self.assertIs(value, ret)

        value = 3.14
        ret = Ordered(gt=3.0, ne=3.1, le=3.14).check(value)
        self.assertIs(value, ret)

        value = 1
        ret = Ordered(ne=0).check(value)
        self.assertIs(value, ret)

        value = -19.0
        ret = Ordered(eq=-19).check(value)
        self.assertIs(value, ret)

        value = -19.0
        ret = Ordered(ge=-19).check(value)
        self.assertIs(value, ret)

        value = 0.5
        ret = Ordered(ge=0.0, le=1.0).check(value)
        self.assertIs(value, ret)

        with self.assertRaises(ValueError):
            Ordered(ne=4).check(4.0)
        with self.assertRaises(ValueError):
            Ordered(eq=4).check(4.1)
        with self.assertRaises(ValueError):
            Ordered(gt=3).check(3)
        with self.assertRaises(ValueError):
            Ordered(le=5.5).check(6)
        with self.assertRaises(ValueError):
            Ordered(ge=0.0, le=1.0).check(1.1)


class TestSized(unittest.TestCase):
    def test_init(self):
        Sized()
        Sized(len_eq=5)
        Sized(len_ge=4)
        Sized(len_ge=0, len_le=10)

        with self.assertRaises(TypeError):
            Sized(len_eq='asd')
        with self.assertRaises(TypeError):
            Sized(len_eq=1, len_ne=1)

    def test_check(self):
        value = [1, 2, 3]
        ret = Sized().check(value)
        self.assertIs(value, ret)

        value = [1, 2, 3]
        ret = Sized(len_ge=0).check(value)
        self.assertIs(value, ret)

        value = [1, 2, 3]
        ret = Sized(len_ge=0, len_le=3).check(value)
        self.assertIs(value, ret)

        value = {}
        ret = Sized(len_eq=0).check(value)
        self.assertIs(value, ret)

        with self.assertRaises(TypeError):
            Sized(len_ne=2).check(True)

        with self.assertRaises(ValueError):
            Sized(len_ne=2).check(dict(a=1, b=2))

        with self.assertRaises(ValueError):
            Sized(len_lt=3).check({1, 'a', 3.14})
