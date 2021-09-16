from collections import OrderedDict
import inspect


class Sentinel:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name


class DocString:
    def __init__(self, doc):
        self.prefix = ''
        self.params = OrderedDict()
        self.suffix = ''
        self.skip_extend = False
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
            # e.g. ":param param_name: *Type* – description." -> "param param_name"
            key = param.split(':')[1]
            self.params[key] = param

    def _parse_docstring(self, doc):
        if doc is None:
            return

        self.skip_extend = ':meta skip-docstring-extend:' in doc

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
        if self.skip_extend:
            return

        for other in others:
            for key, value in other.params.items():
                if key not in self.params:
                    self.params[key] = value


def extend_docstring(cls):
    cls_doc, *bases_docs = [DocString.from_class(base) for base in inspect.getmro(cls)]
    cls_doc.extend_params(bases_docs)

    cls.__doc__ = cls_doc.to_string()
