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
            CheckerLike().check(1)
            CheckerLike().check('abcd')
            CheckerLike().check(tuple())
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
            Typed(1)
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
            Typed(str).check(0x1234)