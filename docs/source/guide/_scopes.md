# Failures' scopes

Usually in production, we want to report any failure that our application encounters, and we want our reports 
to be as specific as possible to reduce the time and effort needed to fix it or label it. 

For that purpose, ``failures`` has a tool to label code parts with meaningful names that we can recognize when seeing
logs and reports, this tools automatically concatenates labels starting from the outer to the most inner to pinpoint
the location where that failure occurred.

This tool is {func}`failures.scope`, it is used as context manager to label, capture errors within its scope 
and handle them if a handler function is provided, the syntax is as follows

{emphasize-lines="5"}
````python
# test1.py
from failures import scope, print_failure

def always_fails():
    with scope("root", print_failure):
        raise Exception("Test exception")

````

The first argument of {func}`failures.scope` is the scope name _(label)_, it's a mandatory attribute.
The second one is optional and in most cases only needed in the outermost layer, this parameter takes a function
to handle those failures, either to log them, run and alternative code, inform the client or whatever logic is suitable
for your specific use case. 

The naming of the scope is validated and must be a non-empty string that only contains ascii letters and/or digits,
optionally a bracket ``[]`` or parenthesis ``()`` containing ascii letters and or digits, 
the name can contain multiple names with that pattern, separated either by dots ``.`` or hyphens ``-``.

This is not a limitation but a validation mechanism that ensures the naming conversion for better reports,
so ``downloading``, ``data(url)``, ``processing_email_2``, ``downloading.retry(2)``, ``loop.iteration[5].add``, ...
are all valid names, but, ``b'downloading'``, ``''``, ``processing..data``, ``'[loop]'`` are all invalid.

The handler function however must be a function or a callable object with a signature 
```(source: str, error: Exception, **kwargs) -> None```, the first positional argument ``source`` contains concatenated
labels pointing to the scope where the failure occurred, and the second positional argument ``error`` is the actual
error captured by {class}`failures.core.Scope` object. 
The ``**kwargs`` arbitrary keyword arguments will be used in future versions to pass additional failure details.

```failures``` is shipped with a default handler _(``print_failure``)_ to get us started,
this handler only logs _(prints)_ failures to the standard output. 

Now with all that covered, let's bring the function we've created to the interpreter and test it.

````pycon
>>> from test1 import always_fails
>>> always_fails()
[FAILURE] root :: Exception(Test exception) 2023-04-10 00:00:00
````
The log states that a failure occurred in ``root`` caused by ``Exception(Test exception)`` 


````{toctree}
    :hidden:
dependent_series.md
scoped_functions.md
handling_manually.md
bound_scopes.md
unbound_scopes.md
````
