from argscheck import List, Typed, Int, Sized, Set


# Sized(len_eq='asd').check([1, 2, 3])
Set(int, ge=1, len_lt=3).check({1,2})
print(Set.__mro__)