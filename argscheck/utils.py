import inspect


class Sentinel:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name


class ParamContainer:
    def __init__(self):
        self.keys = []
        self.values = []

    def __len__(self):
        return len(self.values)

    def __getitem__(self, item):
        return self.values[item]

    def add(self, param):
        # e.g. ":param param_name: *Type* – description." -> "param param_name"
        key = param.split(':')[1]

        if key in self.keys:
            return

        self.keys.append(key)
        self.values.append(param)

    def extend(self, params):
        for param in params:
            self.add(param)


def split_and_keep(string, sep):
    parts = string.split(sep)[1:]
    parts = [sep + part for part in parts]

    return parts


def extract_params(cls):
    doc = cls.__doc__

    if doc is None:
        return []

    doc = doc.split(':Example:')[0]
    doc = doc[doc.find(':param'):]
    params = split_and_keep(doc, ':param')

    return params


def insert_params(cls, params):
    doc = cls.__doc__

    if doc is None:
        return

    prefix = doc.split(':param')[0]
    suffix = ''.join(split_and_keep(doc, ':Example:'))
    doc = prefix + ''.join(params) + suffix

    cls.__doc__ = doc


def extend_docstring(cls):
    params = ParamContainer()

    for base in inspect.getmro(cls):
        params.extend(extract_params(base))

    insert_params(cls, params)

    return cls
