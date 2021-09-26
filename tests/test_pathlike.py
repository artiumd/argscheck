from pathlib import Path

from argscheck import PathLike

from tests.argscheck_test_case import TestCaseArgscheck


class TestPathLike(TestCaseArgscheck):
    def test_init(self):
        # Good arguments
        PathLike()
        PathLike(is_dir=True)
        PathLike(is_file=True)
        PathLike(suffix='.exe')
        PathLike(suffixes=['.exe'])
        PathLike(suffix='.exe', suffixes=['.exe'])

        # Bad arguments
        self.assertRaises(TypeError, PathLike, is_dir=1)
        self.assertRaises(TypeError, PathLike, is_file=None)
        self.assertRaises(ValueError, PathLike, is_file=True, is_dir=True)
        self.assertRaises(ValueError, PathLike, suffix='exe')
        self.assertRaises(TypeError, PathLike, suffixes='.exe')
        self.assertRaises(TypeError, PathLike, suffixes=('.exe',))
        self.assertRaises(ValueError, PathLike, as_path=True, as_str=True)

    def test_check(self):
        self.checker = PathLike()
        self.assertOutputIsInput('abcd')
        self.assertOutputIsInput(Path('abcd'))
        self.assertRaisesOnCheck(TypeError, 0x1234)
        self.assertRaisesOnCheck(TypeError, b"abcd")

        self.checker = PathLike(suffix='.exe')
        self.assertOutputIsInput('abcd.exe')
        self.assertOutputIsInput(Path('abcd.exe'))
        self.assertRaisesOnCheck(ValueError, 'abcd.ex')
        self.assertRaisesOnCheck(ValueError, Path('abcd.exe.gz'))

        self.checker = PathLike(suffixes=['.tar', '.gz'])
        self.assertOutputIsInput('abcd.tar.gz')
        self.assertOutputIsInput(Path('abcd.tar.gz'))
        self.assertRaisesOnCheck(ValueError, 'abcd.tar')
        self.assertRaisesOnCheck(ValueError, Path('abcd.exe.gz'))

        self.checker = PathLike(suffix='.exe', suffixes=['.tar', '.gz'])
        self.assertOutputIsInput('abcd.tar.gz')
        self.assertOutputIsInput(Path('abcd.tar.gz'))
        self.assertOutputIsInput('abcd.exe')
        self.assertOutputIsInput(Path('abcd.exe'))
        self.assertRaisesOnCheck(ValueError, 'abcd.ex')
        self.assertRaisesOnCheck(ValueError, Path('abcd.exe.gz'))
        self.assertRaisesOnCheck(ValueError, 'abcd.tar')
        self.assertRaisesOnCheck(ValueError, Path('abcd.exe.gz'))
