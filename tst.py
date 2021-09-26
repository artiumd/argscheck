import inspect


def greatest_common_base(*types):
    types = set(types)

    mros = [reversed(inspect.getmro(typ)) for typ in types]

    common = None

    for bases in zip(*mros):
        bases_set = set(bases)

        if len(bases_set) == 1:
            common = bases[0]
        else:
            break

    return common


def greatest_common_base(*types):
    return sorted(types, key=lambda a, b: issubclass(a, b))


from collections import defaultdict


class A:
    pass

class B(A):
    pass

class C(A):
    pass

class D(B):
    pass

class E(D):
    pass

print(greatest_common_base(D, E))
