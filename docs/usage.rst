Usage Patterns
==============

There are a number ways to use :mod:`argscheck`, the ultimate choice will usually depend on the particular use case and
the user's preference.

Standalone
----------

This is the most straightforward way: call :func:`~argscheck.core.check` with the checker object and the argument's value.

Example:

.. code-block:: python

    from argscheck import check, Sequence, Optional, PositiveInt


    positives = Sequence(Optional(PositiveInt, default_value=0))

    check(positives, [1, 2, 3])     # Passes, [1, 2, 3] os returned
    check(positives, (1, 2, None))  # Passes, (1, 2, 0) is returned
    check(positives, [1, 2, -3])    # Fails, a ValueError is raised

For more details see documentation of :func:`~argscheck.core.check`.

Decorator
---------

Using the :func:`~argscheck.core.check_args` decorator we can check (and possibly convert) arguments of a function or method. The check is
done automatically on each function call.

Example:

.. code-block:: python

    from argscheck import check_args, Sequence, Optional, PositiveInt


    @check_args
    def add(positives: Sequence(Optional(PositiveInt, default_value=0))):
        return sum(positives)


    add([1, 2, 3])     # Passes, 6 is returned
    add((1, 2, None))  # Passes, 3 is returned
    add([1, 2, -3])    # Fails, a ValueError is raised

For more details see documentation of :func:`~argscheck.core.check_args`


``pydantic`` Validator
----------------------

This method allows us to use :mod:`argscheck` together with `pydantic <https://pydantic-docs.helpmanual.io/>`_.

Using the :func:`~argscheck.core.validator` function, we can create a `validator <https://pydantic-docs.helpmanual.io/usage/validators/>`_
just like with a ``pydantic.validator`` decorator.

Example:

.. code-block:: python

    from typing import Any

    from pydantic import BaseModel
    from argscheck import validator, Sequence, PositiveInt, Optional


    class UserModel(BaseModel):
        positives: Any
        check_positives = validator(Sequence(Optional(PositiveInt, default_value=0)), 'positives')


    UserModel(positives=[1, 2, 3]).positives     # Returns [1, 2, 3]
    UserModel(positives=(1, 2, None)).positives  # Returns (1, 2, 0)
    UserModel(positives=[1, 2, -3]).positives    # Raises ValueError

For more details see documentation of :func:`~argscheck.core.validator`