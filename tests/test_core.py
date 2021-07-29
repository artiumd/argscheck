import unittest

from argscheck import Checker, Typed, Ordered, Sized, One


class TestTyped(unittest.TestCase):
    def test_init(self):
        # Zero arguments
        with self.assertRaises(TypeError):
            Typed()

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
        Typed(int, float)
        Typed(int, bool, list, dict)

    def test_check(self):
        value = 1e5
        typed = Typed(float)
        ret = typed.check(value)
        self.assertIs(ret, value)

        value = True
        typed = Typed(int)
        ret = typed.check(value)
        self.assertIs(ret, value)

        value = [1, 2, 3]
        typed = Typed(list)
        ret = typed.check(value)
        self.assertIs(ret, value)

        typed = Typed(Typed)
        ret = typed.check(typed)
        self.assertIs(ret, typed)

        typed = Typed(int, float)
        value = -12
        ret = typed.check(value)
        self.assertIs(ret, value)

        value = 1.234
        ret = typed.check(value)
        self.assertIs(ret, value)

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
        with self.assertRaises(TypeError):
            Ordered(ge=0.0).check('1.1')


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


class TestOne(unittest.TestCase):
    def test_init(self):
        One(int, float)
        One(Ordered(), Sized())
        One(Ordered, Sized)
        One(Ordered, int)

        with self.assertRaises(TypeError):
            One()
        with self.assertRaises(TypeError):
            One(int)
        with self.assertRaises(TypeError):
            One(int, None)
        with self.assertRaises(TypeError):
            One(str, 2)

    def test_check(self):
        int_or_str = One(int, str)
        value = 'abcd'
        ret = int_or_str.check(value)
        self.assertIs(ret, value)
        value = 1234
        ret = int_or_str.check(value)
        self.assertIs(ret, value)
        value = True
        ret = int_or_str.check(value)
        self.assertIs(ret, value)

        with self.assertRaises(Exception):
            int_or_str.check(1.1)

        sized_list = One(Sized, list)
        with self.assertRaises(Exception):
            sized_list.check([])

        int_or_bool = One(int, bool)
        value = int(1e5)
        ret = int_or_bool.check(value)
        self.assertIs(value, ret)
        with self.assertRaises(Exception):
            int_or_bool.check(True)

        one = One(float, str, bool, Sized(len_eq=2))
        value = 1.234
        ret = one.check(value)
        self.assertIs(value, ret)
        value = 'abcd'
        ret = one.check(value)
        self.assertIs(value, ret)
        value = {1, 'a'}
        ret = one.check(value)
        self.assertIs(value, ret)

        with self.assertRaises(Exception):
            one.check([1, 2, 3])
            one.check(1)