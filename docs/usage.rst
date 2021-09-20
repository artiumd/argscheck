Usage Patterns
==============

There are a number ways to use :mod:`argscheck`, the ultimate choice will usually depend on the particular use case and
the user's preference.

Standalone
----------

This is the most straightforward way and it involves calling a checker's ``check()`` method on an argument.

Example:

.. code-block:: python

    from argscheck import Sequence, Optional, PositiveInt


    positives = Sequence(Optional(PositiveInt, default_value=0))

    positives.check([1, 2, 3])              # Returns [1, 2, 3]
    positives.check(pos_nums=(1, 2, None))  # Returns (1, 2, 0)
    positives.check([1, 2, -3])             # Raises ValueError

For a more details see: :meth:`argscheck.core.Checker.check`

Decorator
---------

Using the ``check_args`` decorator we can check (and possibly convert) arguments of a function or method. The check is
done automatically on each function call.

Example:

.. code-block:: python

    from argscheck import Sequence, Optional, PositiveInt, check_args


    @check_args
    def add(positives: Sequence(Optional(PositiveInt, default_value=0))):
        return sum(positives)

    add([1, 2, 3])     # Returns 6
    add((1, 2, None))  # Returns 3
    add([1, 2, -3])    # Raises ValueError

For a more details see: :func:`argscheck.core.check_args`


``pydantic`` Validator
----------------------

This method allows us to use :mod:`argscheck` together with `pydantic <https://pydantic-docs.helpmanual.io/>`_.

Using the ``validator()`` method, we can create a `validator <https://pydantic-docs.helpmanual.io/usage/validators/>`_
just like with a ``pydantic.validator`` decorator.

Example:

.. code-block:: python

    from typing import Any

    from pydantic import BaseModel
    from argscheck import Sequence, PositiveInt, Optional


    class UserModel(BaseModel):
        positives: Any
        check_positives = Sequence(Optional(PositiveInt, default_value=0)).validator('positives')


    UserModel(positives=[1, 2, 3]).positives     # Returns [1, 2, 3]
    UserModel(positives=(1, 2, None)).positives  # Returns (1, 2, 0)
    UserModel(positives=[1, 2, -3]).positives    # Raises ValueError

For a more details see: :meth:`argscheck.core.Checker.validator`