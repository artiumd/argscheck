from .core import Checker, validate_checker_like


class Iterator(Checker):
    def __init__(self, *checker_likes):
        self.checker = validate_checker_like(self, 'checker_likes', checker_likes)
        self.name = self.value = self.i = self.iter = None

    def check(self, *args, **kwargs):
        name, value = self._resolve_check_args(*args, **kwargs)
        return self.__call__(name, value)

    def __call__(self, name, value):
        self.name = "{}'th item from " + str(name)
        self.value = value
        self.i = 0

        return self

    def __next__(self):
        name = self.name.format(self.i)
        self.i += 1
        value = next(self.iter)
        passed, value = self.checker(name, value)

        if not passed:
            raise value

        return value


class Iterable(Iterator):
    def __iter__(self):
        self.iter = iter(self.value)

        return self
