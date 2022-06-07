from argscheck import Sized, One, Comparable, String, Int, Iterable, Iterator

from tests.argscheck_test_case import TestCaseArgscheck
from tests.mocks import MockIterable, MockIterator


class TestTyped(TestCaseArgscheck):
    def test_check(self):
        self.checker = float
        self.assertOutputIsInput(0.0)
        self.assertOutputIsInput(1e5)
        self.assertOutputIsInput(float('nan'))
        self.assertOutputIsInput(float('inf'))
        self.assertOutputIsInput(float('-inf'))
        self.assertRaisesOnCheck(TypeError, 1)

        self.checker = int
        self.assertOutputIsInput(True)
        self.assertOutputIsInput(-1234)
        self.assertRaisesOnCheck(TypeError, 1e5)

        self.checker = list
        self.assertOutputIsInput(['', {}, [], ()])
        self.assertOutputIsInput([])
        self.assertRaisesOnCheck(TypeError, {})
        self.assertRaisesOnCheck(TypeError, ())

        self.checker = (int, float)
        self.assertOutputIsInput(-12)
        self.assertOutputIsInput(1.234)

        self.checker = bool
        self.assertOutputIsInput(False)
        self.assertRaisesOnCheck(TypeError, 1)  # 1 is not a bool
        self.assertRaisesOnCheck(TypeError, None)

        self.checker = str
        self.assertOutputIsInput('')
        self.assertOutputIsInput('abcd')
        self.assertRaisesOnCheck(TypeError, 0x1234)

        self.checker = object
        self.assertOutputIsInput('')
        self.assertOutputIsInput([])
        self.assertOutputIsInput(0)
        self.assertOutputIsInput([[[]]])
        self.assertOutputIsInput(object)
        self.assertOutputIsInput(object())
        self.assertOutputIsInput(type)


class TestOne(TestCaseArgscheck):
    def test_init(self):
        # Good arguments
        One(Comparable(), Sized())
        One(Comparable, Sized)
        One(Comparable, int)

        # Bad arguments
        self.assertRaises(TypeError, One)
        self.assertRaises(TypeError, One, int)
        self.assertRaises(TypeError, One, int, float)
        self.assertRaises(TypeError, One, int, None)
        self.assertRaises(TypeError, One, str, 2)

    def test_check(self):
        self.checker = (int, String)
        self.assertOutputIsInput('abcd')
        self.assertOutputIsInput(1234)
        self.assertOutputIsInput(True)
        self.assertRaisesOnCheck(Exception, 1.1)

        self.checker = One(Int, bool)
        self.assertOutputIsInput(int(1e5))
        self.assertRaisesOnCheck(Exception, True)  # True is both an int and a bool

        self.checker = One(float, str, bool, Sized(len_eq=2))
        self.assertOutputIsInput(1.234)
        self.assertOutputIsInput('abcd')
        self.assertOutputIsInput({1, 'a'})
        self.assertRaisesOnCheck(Exception, [1, 2, 3])
        self.assertRaisesOnCheck(Exception, 1)

        self.checker = (Sized, list)
        self.assertRaisesOnCheck(Exception, [])  # [] is both a list and has a length

        self.checker = (int, Iterable[int])
        self.assertRaisesOnCheck(NotImplementedError, 1)
        self.assertRaisesOnCheck(NotImplementedError, MockIterable([1, 2, 3]))

        self.checker = (int, Iterator[int])
        self.assertRaisesOnCheck(NotImplementedError, 1)
        self.assertRaisesOnCheck(NotImplementedError, MockIterator([1, 2, 3]))
