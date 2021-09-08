from argscheck import List, Typed, Int, Sized, Set, One, PathLike


# One(int, One(list, set)).check(1.1)
PathLike(suffix='', suffixes=['.nii', '.gz']).check('asdasd')