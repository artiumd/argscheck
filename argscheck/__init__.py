__all__ = []


def export(definition):
    globals()[definition.__name__] = definition
    __all__.append(definition.__name__)

    return definition


from . import collection, core, iter, numeric, pathlike, sequence, string


__version__ = '1.0.0'
