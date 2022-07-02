from argscheck import Sized, Float, Number, check_args, NonEmpty

from tests.argscheck_test_case import TestCaseArgscheck


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

        self.checker = Sized(len_eq=3)
        self.assertOutputIsInput(['a', 'b', 'c'])
        self.assertOutputIsInput('abc')
        self.assertRaisesOnCheck(ValueError, {'a', 'b'})
        self.assertRaisesOnCheck(TypeError, 123)


class TestFloat(TestCaseArgscheck):
    def test_check(self):
        self.checker = Float()
        self.assertOutputIsInput(1.1)
        self.assertRaisesOnCheck(TypeError, 1)

        self.checker = Float(gt=0.0)
        self.assertOutputIsInput(1.1)
        self.assertRaisesOnCheck(TypeError, 1)
        self.assertRaisesOnCheck(ValueError, 0.0)
        self.assertRaisesOnCheck(ValueError, -1.0)

        self.checker = Float(gt=0.0, le=1.0)
        self.assertOutputIsInput(1.0)
        self.assertOutputIsInput(0.5)
        self.assertRaisesOnCheck(ValueError, 1.1)
        self.assertRaisesOnCheck(ValueError, 0.0)
        self.assertRaisesOnCheck(ValueError, -1.0)

        self.checker = Float(ge=0.0, lt=1.0)
        self.assertOutputIsInput(0.0)
        self.assertOutputIsInput(0.5)
        self.assertRaisesOnCheck(ValueError, 1.0)
        self.assertRaisesOnCheck(ValueError, 1.1)
        self.assertRaisesOnCheck(ValueError, -1.0)

        self.checker = Float(ne=0.0)
        self.assertOutputIsInput(-1.0)
        self.assertOutputIsInput(0.5)
        self.assertRaisesOnCheck(ValueError, 0.0)

        self.checker = Float < 1.0
        self.assertOutputIsInput(0.99)
        self.assertRaisesOnCheck(ValueError, 1.0)

        self.checker = 1.0 > Float
        self.assertOutputIsInput(0.99)
        self.assertRaisesOnCheck(ValueError, 1.0)

        self.checker = 0.0 <= (Float <= 1.0)
        self.assertOutputIsInput(0.5)
        self.assertOutputIsInput(1.0)
        self.assertOutputIsInput(0.0)
        self.assertRaisesOnCheck(ValueError, 1.1)
        self.assertRaisesOnCheck(ValueError, -0.9)

        @check_args
        def fun(x: 0.0 <= (Float <= 1.0)):
            pass

        fun(0.0)
        fun(0.5)
        fun(1.0)
        self.assertRaises(ValueError, fun, 1.1)
        self.assertRaises(TypeError, fun, 2)


class TestNumber(TestCaseArgscheck):
    def test_check(self):
        self.checker = Number != 6
        self.assertOutputIsInput(0.99)
        self.assertRaisesOnCheck(ValueError, 6)
        self.assertRaisesOnCheck(ValueError, 6.0)

        self.checker = 6 == Number
        self.assertOutputIsInput(6)
        self.assertOutputIsInput(6.0)
        self.assertRaisesOnCheck(ValueError, 1)

        self.checker = Number(ge=0, lt=10)
        self.assertOutputIsInput(0)
        self.assertOutputIsInput(5.0)
        self.assertRaisesOnCheck(ValueError, 10)
        self.assertRaisesOnCheck(TypeError, 'a')

        self.checker = 0 <= (Number < 10)
        self.assertOutputIsInput(0)
        self.assertOutputIsInput(5.0)
        self.assertRaisesOnCheck(ValueError, 10)
        self.assertRaisesOnCheck(TypeError, 'a')

        self.checker = (0.0 <= (Number < 25)) != 14
        self.assertOutputIsInput(0)
        self.assertOutputIsInput(11.0)
        self.assertRaisesOnCheck(ValueError, 26)
        self.assertRaisesOnCheck(ValueError, 14)
        self.assertRaisesOnCheck(TypeError, 'a')


class TestNonEmpty(TestCaseArgscheck):
    def test_check(self):
        self.checker = NonEmpty
        self.assertOutputIsInput(['a', 'b', 'c'])
        self.assertOutputIsInput('abc')
        self.assertRaisesOnCheck(ValueError, '')
        self.assertRaisesOnCheck(ValueError, [])
        self.assertRaisesOnCheck(TypeError, 0)
        self.assertRaisesOnCheck(TypeError, None)
