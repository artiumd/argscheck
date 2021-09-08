from argscheck import Comparable, Sized

from tests.argscheck_test_case import TestCaseArgscheck


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

        self.checker = Sized()
        self.assertOutputIsInput([1, 2, 3])
        self.assertRaisesOnCheck(TypeError, 1)
