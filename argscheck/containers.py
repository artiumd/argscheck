from .core import Sized, Typed, validate_checker_like


class Sequence(Sized, Typed):
    type_ = object

    def __init__(self, *checker_likes, **kwargs):
        super().__init__(self.type_, **kwargs)

        self.item_checker = validate_checker_like(self, 'checker_likes', checker_likes)

    def _item_iter(self, name, value):
        for i, item in enumerate(value):
            passed, item = self.item_checker(f'{name}[{i}]', item)

            if not passed:
                raise item

            yield item

    def __call__(self, name, value):
        passed, value = super().__call__(name, value)
        if not passed:
            return False, value

        type_ = type(value)

        try:
            value = type_(self._item_iter(name, value))
        except Exception as e:
            return False, e

        return True, value


class Tuple(Sequence):
    type_ = tuple


class List(Sequence):
    type_ = list


class Set(Sequence):
    type_ = set
