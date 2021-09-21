from argscheck import Typed, Optional, String, One, Sized, Comparable, Int, NonEmpty, Iterable, Collection

# Optional(int, float, String('.')).check(arg='a/')
# Typed(int, str).check(None)
# Int(gt=0, ne=1).check('')
# NonEmpty(len_gt=3).check([])
# Sized(len_gt=2).check([1])
# list(Iterable(str).check(['a', 1]))
Collection(str).check({'a', 1})