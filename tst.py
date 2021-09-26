from argscheck import Optional,Sequence


class Descriptor:
    __slots__ = ('checker', 'name')

    def __init__(self, checker):
        self.checker = checker

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        return instance.__dict__[self.name]

    def __set__(self, instance, value):
        instance.__dict__[self.name] = self.checker._check(self.name, value)


class A:
    a = Descriptor(Optional(int, default_value=55))
    b = Optional(int, default_value=55)

    def __init__(self, a):
        self.a = a


a = A(1)
print(a.a)
a = A(None)
print(a.a)
# A('a')

Sequence(int).check(zzz=[1,2,'a'])