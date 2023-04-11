<div id="readme_header" style="text-align: center">
<h1 style="color: #913946ff; font-family: Candara, sans-serif;">Failures</h1>
<p style="color: #bf6572; font-family: Candara, sans-serif; font-style: italic">Labeling failures for humans</p>
<br/>
<a href="https://github.com/mediadnan/Failures/actions/workflows/tests.yml" target="_blank"><img src="https://github.com/mediadnan/Failures/actions/workflows/tests.yml/badge.svg" alt="Tests"/></a>
<a href="https://codecov.io/gh/mediadnan/Failures" target="_blank"><img src="https://codecov.io/gh/mediadnan/Failures/branch/main/graph/badge.svg?token=E58PJ3OFME" alt="CodeCov"/></a>
<a href="https://www.python.org/downloads/" target="_blank"><img src="https://img.shields.io/pypi/pyversions/failures" alt="PyPI - Python Version"/></a>
<a href="https://failures.readthedocs.io/" target="_blank"><img alt="Read the Docs" src="https://img.shields.io/readthedocs/failures"></a>
<a href="https://en.wikipedia.org/wiki/MIT_License" target="_blank"><img src="https://img.shields.io/github/license/mediadnan/failures" alt="License"/></a>
<a href="https://github.com/mediadnan/Failures/issues" target="_blank"><img src="https://img.shields.io/github/issues/mediadnan/failures" alt="GitHub issues" /></a>
<a href="https://pypi.org/project/failures/" target="_blank"><img alt="PyPI - Downloads" src="https://img.shields.io/pypi/dm/failures"></a>
</div>

## What is failures
Failures is a python3 package that provides utilities to explicitly label nested
failures _(errors)_ with simple syntax, and gives better flexibility on what errors
to handle and how to handle them.

## Installation
``failures`` is available at PyPI, and requires python 3.8 or higher,
install it by executing the pip command:

```shell
pip install failures
```

> **Note**
> This package comes with a default handler that prints failures to the standard output,
> if you want them to be highlighted with colors, you can install ``pip install "failures[colors]"``

## Usage
### Failures scope _(context)_ 
This example will showcase the use of ``failure.scope`` to create a labeled failures scope and handle them
in the outermost ``Scope`` layer.

Let's create a file ``example.py``
````python
import math
import failures


def data_num_inverse_sqrt(data: dict) -> float:
    with failures.scope("number", show_failure):
        with failures.scope("extract"):
            num = data["num"]  # fails if 'num' not in data or data is not a dict (1)
        with failures.scope("convert"):
            num = int(num)  # fails if num is not a sequence of digits (2)
        with failures.scope("evaluate"):
            return inverse_sqrt(num)


def inverse_sqrt(num: int) -> float:
    # independent (decoupled) function
    with failures.scope("inverse"):
        num = 1 / num  # fails if num == 0 (3)
    with failures.scope("square_root"):
        return round(math.sqrt(num), 2)  # fails if num < 0 (4)


def show_failure(label: str, error: Exception) -> None:
    # This function will serve as a failure handler
    # and will simply print the source and the error
    print(f"[{label}] {error!r}")

````
The code is self-explanatory, ``data_num_inverse_sqrt`` function is the outer layer function that expects
exactly a ``dict`` _(or a map-like object)_ that has a non-null positive number exactly with the key ``'num'``,
this function also uses an independent function ``inverse_sqrt`` that might also fail,
and finally we implement our own simple function for handling failures ``show_failure``.

````pycon
>>> from example import data_num_inverse_sqrt
>>> data_num_inverse_sqrt(5)  # (1)
[number.extract] TypeError("'int' object is not subscriptable")

>>> data_num_inverse_sqrt({'my_num': 5})  # (1)
[number.extract] KeyError('num')

>>> data_num_inverse_sqrt({"num": "two"})  # (2)
[number.convert] ValueError("invalid literal for int() with base 10: 'two'")

>>> data_num_inverse_sqrt({"num": "0"})  # (3)
[number.evaluate.inverse] ZeroDivisionError('division by zero')

>>> data_num_inverse_sqrt({"num": "-5"})  # (4)
[number.evaluate.square_root] ValueError('math domain error')

>>> data_num_inverse_sqrt({"num": "4"})  # No errors
0.5

>>> data_num_inverse_sqrt({"num": 4}) # same, no errors
0.5
````
Each scoped context captures any raised exception withing its scope and tag it with its label,
then either handles it if a handler function was passed to it or re-raise it to the outer layer
scope, each failures' scope captures a tagged and prepends its label until reaching the top level one. 

### Failures scoped _(decorator)_
The ``failures.scoped`` decorator is used to wrap a function within a labeled
scope to reduce indentation and redundancy.

Sot this function
````python
def number_processing(number):
    with failures.scope("number_processing"):   # label same as function name
        with failures.scope("step1"):
            ...
        with failures.scope("step2"):
            ...
````
can be replaced by
````python
@failures.scoped
def number_processing(number):
    with failures.scope("step1"):
        ...
    with failures.scope("step2"):
        ...
````
The decorator can also take optional parameters to customize the ``Scope`` object wrapping the function
````python
def number_processing(number):
    with failures.scope("processing", show_failure):
        with failures.scope("step1"):
            ...
        with failures.scope("step2"):
            ...
````
can be replaced by
````python
@failures.scoped(name="processing", handler=show_failure)
def number_processing(number):
    with failures.scope("step1"):
        ...
    with failures.scope("step2"):
        ...
````

### Failures handler
The ``failures.handler`` utility creates a custom failure handler with additional filters,
this function takes one required positional-only argument for the actual failure handling function,
and two optional keyword-only argument, ``ignore`` to mark failures that should be ignored _(suppressed)_,
and ``propagate`` to mark failures that shouldn't be captured _(unhandled)_.

``ignore`` and ``propagate`` can take an exception type _(like ``ValueError``)_, or a tuple of
exception types.

````pycon
>>> from failures import scope, handler
>>> from example import show_failure
>>> def my_function(error: Exception):
...     with scope('test_handler', handler(show_failure, ignore=KeyError, propagate=TypeError)):
...         raise error
...

>>> my_function(ValueError("value error"))  # Handled
[test_handler] ValueError('value error')
>>> my_function(TypeError("value error"))  # Unhandled
Traceback (most recent call last):
    ...
failures.core.Failure: ('test_handler', TypeError('value error'))
>>> my_function(TypeError("type error"))  # Ignored
>>>
````
