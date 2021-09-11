from argscheck import List, Typed, Int, Sized, Set, One, PathLike, Sequence, MutableSequence


# One(int, One(list, set)).check(1.1)
# PathLike(suffix='.j', suffixes=['.nii', '.gz']).check('asdasd.j')
# One(int, One(float, str)).check(1+1j)
Sequence(int).check([1,2,3])
MutableSequence(int).check((1,2,3))
