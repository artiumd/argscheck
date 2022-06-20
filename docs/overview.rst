Overview
========

The :mod:`argscheck` library provides means for simple but comprehensive argument checking for Python.

The main highlights are:

* No need for repetitive and error-prone boilerplate code.

    * This results in more readable code.

* Besides argument checking, argument conversion can also take place.

    * See next example.

* Compose simple building blocks to perform complex checks.

    * e.g. ``Optional(Sequence(ExistingFile(as_path=True, suffix='.xml')), default_factory=list)`` -

        * Checks if argument is ``None``, if it is, replace it with a fresh list instance.
        * Otherwise, check if argument is a sequence, in which, each item is an existing `.xml` files (each file is a ``pathlib.Path`` or ``str``
          object).
        * Additionally, convert each file to a ``pathlib.Path`` object if it is a string.

* Automatically throws exceptions with informative error messages.

    * Bugs are detected more quickly.

* :mod:`argscheck` closely follows the Python data model.

    * Checking is oriented towards behaviour rather than typing.
