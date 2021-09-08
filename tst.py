from argscheck import List, Typed, Int, Sized, Set, One


One(int, One(list, set)).check(1.1)