from argscheck import Sized, Float

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
