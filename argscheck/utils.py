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
        assert param.startswith(':param '), param
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

    idx = doc.find(':param')

    if idx == -1:
        return []

    doc = doc[idx:]
    params = split_and_keep(doc, ':param')

    return params


def take_before(string, before):
    return string[:string.find(before)]


def insert_params(cls, params):
    doc = cls.__doc__

    if doc is None:
        return

    # Build prefix
    # prefix = take_before(doc, ':Example:')
    # prefix = take_before(prefix, ':param')

    if ':param' not in doc:
        idx = doc.find(':Example:')
        prefix = doc[:idx]
    else:
        prefix = doc.split(':param')[0]

    # Build suffix
    if ':Example:' not in doc:
        suffix = ''
    else:
        suffix = ''.join(split_and_keep(doc, ':Example:'))

    doc = prefix + ''.join(params) + suffix

    cls.__doc__ = doc


def extend_docstring(cls):
    doc = cls.__doc__

    if doc is None or doc.startswith('\n    Same as :class:`'):
        return

    params = ParamContainer()

    for base in inspect.getmro(cls):
        params.extend(extract_params(base))

    insert_params(cls, params)
