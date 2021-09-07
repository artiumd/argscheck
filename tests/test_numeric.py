from argscheck import Ordered, Sized

from tests.argscheck_test_case import TestCaseArgscheck


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