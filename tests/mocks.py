class MockClass:
    pass


class MockCollection:
    def __init__(self, items):
        self.items = list(items)

    def __iter__(self):
        return iter(self.items)

    def __len__(self):
        return len(self.items)

    def __eq__(self, other):
        return set(self) == set(other)


class MockIterable:
    def __init__(self, values):
        self.values = values

    def __iter__(self):
        return MockIterator(self.values)


class MockIterator:
    def __init__(self, values):
        self.values = values
        self.i = 0

    def __next__(self):
        if self.i == len(self.values):
            raise StopIteration
        else:
            ret = self.values[self.i]
            self.i += 1

            return ret
