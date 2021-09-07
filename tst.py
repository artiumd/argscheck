from argscheck import List, Typed, Int


Typed(set, int).check(1)
# List(len_ne=2).check(a=[1,1])
Int(ge=4).check(1)