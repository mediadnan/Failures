# Multiple sub scopes
Our code is mostly made of a series of instructions that each depends on the previous, and often needs to be separated
smaller logical entities. In our context, we can use {func}`failures.scope` to mark different scopes,
and handle the entire block with a top level ``scope``.

````python
# test2.py
from failures import scope, print_failure


def inp_validation(inp: int) -> None:
    with scope('inp_validation', print_failure):
        with scope('check_1'):
            print("scope_1 executed")
            assert inp != 3, "cannot use 3"
        with scope('check_2'):
            print("scope_2 executed")
            assert inp != 5, "cannot use 5 too"
        with scope('check_3'):
            print("scope_3 executed")
            assert inp >= 0, "positive numbers only"

````

Unlike the previous example, in this one we separated our function into three sub scopes ``check_1``, ``check_2`` 
and ``check_3``, each scope can raise an ``AssertionError``, and we want our function to stop and omit the remaining 
instructions if any of the blocks fails.

````{note}
We didn't pass the handler ``print_failure`` to the inner scopes, we only want to handle failures at the top level scope.
````

Now if we bring our function to the interpreter and test it, we get

````pycon
>>> from test2 import inp_validation
>>> inp_validation(3)
scope_1 executed
[FAILURE] inp_validation.check_1 :: AssertionError(cannot use 3) 2023-04-10 00:00:00
>>> inp_validation(5)
scope_1 executed
scope_2 executed
[FAILURE] inp_validation.check_2 :: AssertionError(cannot use 5 too) 2023-04-10 00:00:00
>>> inp_validation(-2)
scope_1 executed
scope_2 executed
scope_3 executed
[FAILURE] inp_validation.check_3 :: AssertionError(positive numbers only) 2023-04-10 00:00:00
>>> inp_validation(1)
scope_1 executed
scope_2 executed
scope_3 executed
````
