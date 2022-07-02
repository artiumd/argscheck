from collections import OrderedDict
import inspect


class Sentinel:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name


def extend_docstring(cls):
    cls_doc, *bases_docs = [_DocString.from_class(base) for base in inspect.getmro(cls)]
    cls_doc.extend_params(bases_docs)
    cls.__doc__ = cls_doc.to_string()


def partition(sequence, condition):
    true, false = [], []

    for item in sequence:
        if condition(item):
            true.append(item)
        else:
            false.append(item)

    return true, false


def join(string, iterable, *, on_empty=None):
    """
    A functional version of ``str.join()`` providing more flexibility via the ``on_empty`` parameter.

    Arguments are not checked.

    :param string:
    :param iterable:
    :param on_empty:
    :return:
    """
    if on_empty == 'drop':
        return string.join(item for item in iterable if item)

    if on_empty == 'abort' and '' in iterable:
        return ''

    return string.join(iterable)


class _DocString:
    def __init__(self, doc):
        self.prefix = ''
        self.params = OrderedDict()
        self.suffix = ''
        self.skipped_params = _ContainsNone()
        self._parse_docstring(doc)

    @classmethod
    def from_class(cls, cls_):
        return cls(cls_.__doc__)

    @staticmethod
    def _split_and_keep(string, sep):
        parts = string.split(sep)[1:]
        parts = [sep + part for part in parts]

        return parts

    def _parse_params(self, params_doc):
        for param in self._split_and_keep(params_doc, ':param'):
            key = param.split(':')[1].split('param ')[1]
            self.params[key] = param

    def _parse_docstring(self, doc):
        if doc is None:
            return

        # Parse ":meta skip-extend-docstring-param_1-param_2-..." directive
        start = doc.find(':meta skip-extend-docstring')
        if start != -1:
            end = doc.find(':', start + 1)
            assert end != -1
            params = doc[start: end].split('-')[3:]

            if params:
                self.skipped_params = set(params)
            else:
                self.skipped_params = _ContainsAll()

        examples_start = doc.find(':Example:')
        params_start = doc.find(':param')

        if examples_start == -1 and params_start == -1:
            # No parameters and no examples were found
            self.prefix = doc

        elif examples_start == -1 and params_start != -1:
            # Only parameters were found
            self.prefix = doc[:params_start]
            self._parse_params(doc[params_start:])

        elif examples_start != -1 and params_start == -1:
            # Only examples were found
            self.prefix = doc[:examples_start]
            self.suffix = doc[examples_start:]

        else:  # examples_start != -1 and params_start != -1
            # Both parameters and examples were found
            self.prefix = doc[:params_start]
            self._parse_params(doc[params_start: examples_start])
            self.suffix = doc[examples_start:]

    def to_string(self):
        return self.prefix + ''.join(self.params.values()) + self.suffix

    def extend_params(self, others):
        for other in others:
            for key, value in other.params.items():
                # Skip if parameter has already been added by a previous base class
                if key in self.params:
                    continue

                if key in self.skipped_params:
                    continue

                # Skip the ``args`` parameter, it should only be taken from the docstring of ``self``
                if key == 'args':
                    continue

                self.params[key] = value


class _ContainsAll:
    def __contains__(self, item):
        return True


class _ContainsNone:
    def __contains__(self, item):
        return False
