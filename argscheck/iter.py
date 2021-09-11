from .core import Checker


class Iterator(Checker):
    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)

        self.item_checker = self._validate_args(args)
        self.name = self.i = self.iterator = None

    def check(self, *args, **kwargs):
        name, value = self._resolve_name_value(*args, **kwargs)

        return self.__call__(name, value)

    def __call__(self, name, value):
        self.name = "{}'th item from " + str(name)
        self.iterator = value
        self.i = 0

        return self

    def __next__(self):
        name = self.name.format(self.i)
        self.i += 1
        value = next(self.iterator)
        passed, value = self.item_checker(name, value)

        if not passed:
            raise value

        return value


class Iterable(Iterator):
    def __iter__(self):
        self.iterator = iter(self.iterator)

        return self
