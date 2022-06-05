from argscheck import Comparable
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

        self.checker = Comparable < 3
        self.assertOutputIsInput(1)
        self.assertOutputIsInput(-1.1)
        self.assertRaisesOnCheck(ValueError, 3)
        self.assertRaisesOnCheck(ValueError, 333.3)
        self.assertRaisesOnCheck(TypeError, 'a')

        self.checker = 3 > Comparable
        self.assertOutputIsInput(1)
        self.assertOutputIsInput(-1.1)
        self.assertRaisesOnCheck(ValueError, 3)
        self.assertRaisesOnCheck(ValueError, 333.3)
        self.assertRaisesOnCheck(TypeError, 'a')
