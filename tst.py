from argscheck import Typed, Optional, String, One, Sized, Comparable, Int, NonEmpty

# Optional(int, float, String('.')).check(arg='a/')
# Typed(int, str).check(None)
# Int(gt=0, ne=1).check('')
NonEmpty().check([])