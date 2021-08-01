from argscheck import Sequence, Optional, List, Tuple, Set


a = Set(Optional(int, default_value=222), len_ge=3).check(a={1, None, -1})
print(a)
