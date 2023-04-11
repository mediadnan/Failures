# Failure scopes

## Introduction
Usually in production, we want to report any failure that our application encounters, and we want it to be as specific
as possible to reduce the time and effort needed to fix it or label it. 
For that purpose, ``failures`` has a tool to label code parts with meaningful names that we can recognize when seeing
logs or reports, so when an error occurs in one part, we get the path of where that error occurred based on those labels.

The tool is {func}`failures.scope`, used as context manager to label and capture errors within its scope and handle them,
The syntax is as follows

````{code-block} python
    :caption: test1.py
from failures import scope, print_failure

def main():
    with scope("root", print_failure):
        raise Exception("Test exception")

````
The first argument of {func}`failures.scope` is the scope label, and it's mandatory as it's the main purpose.
The second one is optional and in most cases only needed in the outermost layer, this parameter takes a function
to handle those failures, either to log them, run and alternative code, inform the client or whatever logic is suitable
for your specific use case. 

The naming of the scope is validated and must be a non-empty string that only contains ascii letters and/or digits,
optionally a bracket ``[]`` or parenthesis ``()`` containing ascii letters and or digits, 
the name can contain multiple names with that pattern separated either by dots ``.`` or hyphens ``-``.

This is not a limitation but a validation mechanism that ensures the naming conversion for better reports,
so ``downloading``, ``data(url)``, ``processing_email_2``, ``downloading.retry(2)``, ``loop.iteration[5].add``, ...
ar all valid names, but, ``b'downloading'``, ``''``, ``processing..data``, ``'[loop]'`` are all invalid.

The handler function however must be a function or a callable object with a signature 
```(source: str, error: Exception, **kwargs) -> None```, the first positional argument ``source`` contains concatenated
labels leading to the scope where the failure occurred, and the second positional argument ``error`` is the actual
error captured by {class}`failures.core.Scope` object. 
The ``**kwargs`` arbitrary keyword arguments will be used in future versions to pass additional failure details.

```failures``` is shipped with a default simple handler _(``print_failure``)_ to get us started,
this handler only logs failures to the standard output. 

Now with all that covered, let's bring the function we've created to the interpreter and test it.

````pycon
>>> from test1 import main
>>> main()
[FAILURE] root :: Exception(Test exception) 2023-04-11 22:50:35
````
The log states that a failure occurred in ``root`` caused by ``Exception(Test exception)`` 

## Series of dependent instructions
Our code is mostly a series of instructions that each depends on the previous, and often needs to be separated
smaller block or logical entities. In our context, we can use {func}`failures.scope` to mark different logical
scopes, and handle the entire block with a top level ``scope``.

````{code-block} python
    :caption: test2.py
from failures import scope, print_failure

def main(inp: int) -> None:
    with scope('inp_validation', print_failure):
        with scope('check_1'):
            assert inp != 3, "cannot use 3"
        with scope('check_2'):
            assert inp != 5, "cannot use 5 too"
        with scope('check_3'):
            assert inp >= 0, "positive numbers only"

````

````{note}
In our examples we'll be focusing on the api syntax, and here we are explicitly causing failures to test
the library api, however in real life scenario, the failure might be caused by some invalid value or runtime error.
````

Unlike the first example, in this one we separated our scope into three sub scopes ``check_1``, ``check_2`` 
and ``check_3``, each scope can raise an ``AssertionError``, and we want our function to stop omit the remaining 
instructions if any of the blocks fails.

````{important}
**Note** that we didn't pass the handler ``print_failure`` to the inner scopes, we only want to handle failures at
the top level scope.
````

Now if we bring our function to the interpreter and test it, we get

````pycon
>>> from test2 import main
>>> main(3)
[FAILURE] inp_validation.check_1 :: AssertionError(cannot use 3) 2023-04-11 23:18:34
>>> main(5)
[FAILURE] inp_validation.check_2 :: AssertionError(cannot use 5 too) 2023-04-11 23:28:07
>>> main(-2)
[FAILURE] inp_validation.check_3 :: AssertionError(positive numbers only) 2023-04-11 23:28:21
>>> main(1)

````


````{toctree}
    :hidden:
unbound_scopes.md
bound_scopes.md
````
