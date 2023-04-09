<div id="readme_header" style="text-align: center">
<h1>Failures</h1>
<i>Labeling failures for humans</i>
<br/><br/>
<a href="https://github.com/mediadnan/Failures/actions/workflows/tests.yml"><img src="https://github.com/mediadnan/Failures/actions/workflows/tests.yml/badge.svg" alt="Tests"/></a>
<a href="https://codecov.io/gh/mediadnan/Failures"><img src="https://codecov.io/gh/mediadnan/Failures/branch/main/graph/badge.svg?token=E58PJ3OFME" alt="CodeCov"/></a>
<a href="https://www.python.org/downloads/"><img src="https://img.shields.io/pypi/pyversions/failures" alt="PyPI - Python Version"/></a>
<a href="https://en.wikipedia.org/wiki/MIT_License"><img src="https://img.shields.io/github/license/mediadnan/failures" alt="License"/></a>
</div>

## What is failures
Failures is a Python 3 module that contains utilities to explicitly label nested
execution errors with fancy and simple syntax without coupling or adding extra ___context___ 
arguments to the targeted functions.

## Installation
``failures`` is available at PyPI, and requires python 3.8 or higher,
you install it using the pip command:

```shell
pip install failures
```

> **Note**
> failures has an official plugin for printing colorful failures,
> you can install it using the command ``pip install "failures[print]"``

## Usage
The ```failures.scope``` is a context manager object that captures failures, labels and handle them.

````python
# example.py

import math
import failures


def inverse_sqrt(num: int) -> float:
    with failures.scope("inverse"):
        num = 1 / num  # fails if num == 0 (3)
    with failures.scope("square_root"):
        return round(math.sqrt(num), 2)  # fails if num < 0 (4)


def add_inverse_sqrt(data: dict) -> float:
    with failures.handle("number", show_failure):
        with failures.scope("extract"):
            num = data["num"]  # fails if 'num' not in data or data is not a dict (1)
        with failures.scope("convert"):
            num = int(num)  # fails if num is not a digit (2)
        with failures.scope("evaluate"):
            return inverse_sqrt(num)


def show_failure(label: str, error: Exception) -> None:
    print(f"[{label}] {error!r}\n")
````

___code explained___

``inverse_sqrt`` is a function that expects a number and evaluates two different operations that
could fail depending on the value of ``num``, ``inverse_sqrt`` is completely decoupled from ``add_inverse_sqrt``
but still, ``add_inverse_sqrt`` can get feedback about the failures that happen inside ``inverse_sqrt``.

``add_inverse_sqrt`` executes its code inside a ``failures.handle`` context that uses ``show_failure`` as handler,
if an error occurs inside any of the scopes, ``show_failure`` will be called with the _dot separated labels_ source
and the actual error that got raised.

Let's test this code with different failing cases:

````pycon
>>> from example import add_inverse_sqrt
>>>
>>> add_inverse_sqrt(5)  # (1)
[number.extract] TypeError("'int' object is not subscriptable")

>>> add_inverse_sqrt({'my_num': 5})  # (1)
[number.extract] KeyError('num')

>>> add_inverse_sqrt({"num": "two"})  # (2)
[number.convert] ValueError("invalid literal for int() with base 10: 'two'")

>>> add_inverse_sqrt({"num": "0"})  # (3)
[number.evaluate.inverse] ZeroDivisionError('division by zero')

>>> add_inverse_sqrt({"num": "-5"})  # (4)
[number.evaluate.square_root] ValueError('math domain error')

>>> add_inverse_sqrt({"num": "4"})  # No errors
0.5
````