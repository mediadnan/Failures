# Scoped functions
To reduce redundancy and indentations, ```failures``` comes with a decorator ({func}`failures.scoped`) 
that wraps functions into a labeled scope, _it's more like a syntax sugar_.

This code function

````python
from math import sqrt
from failures import scope, print_failure

def inverse_sqrt(number: str | int) -> float | None:
    with scope("inverse_sqrt", print_failure):
        with scope("parse_int"):
            number = int(number)
        with scope("sqrt"):
            sqrt_num = sqrt(number)
        with scope("inverse"):
            inv_num = 1/sqrt_num
        return round(inv_num, 3)
````
Can be refactored to 
````python
# test3.py
from math import sqrt
from failures import scope, scoped, print_failure

@scoped(handler=print_failure)
def inverse_sqrt(number: str | int) -> float | None:
    with scope("parse_int"):
        number = int(number)
    with scope("sqrt"):
        sqrt_num = sqrt(number)
    with scope("inverse"):
        inv_num = 1/sqrt_num
    return round(inv_num, 3)
````
The {func}`failures.scoped` decorator's parameters are all optional, in this case the name of scope
was inferred from the function's name, so the entire function scope will be labeled ``'inverse_sqrt'``.

let's test our decorated function.
````pycon
>>> from test3 import inverse_sqrt
>>> # valid inputs
>>> inverse_sqrt("25")
0.2
>>>  inverse_sqrt(4)
0.5
>>>  # invalid inputs
>>> inverse_sqrt("sixteen")
[FAILURE] inverse_sqrt.parse_int :: ValueError(invalid literal for int() with base 10: 'sixteen') 2023-04-10 00:00:00
>>> inverse_sqrt(-4)
[FAILURE] inverse_sqrt.sqrt :: ValueError(math domain error) 2023-04-10 00:00:00
>>> inverse_sqrt("0")
[FAILURE] inverse_sqrt.inverse :: ZeroDivisionError(float division by zero) 2023-04-10 00:00:00
````
If we want to override the default function name, we can pass a new one as keyword argument ``name``, like
````python
import failures

@failures.scoped(name="inverting_square_root", handler=failures.print_failure)
def inverse_sqrt(number: str | int) -> float | None: ...
````

And often we avoid passing a local handler to scoped functions _(we will cover why in next sections)_ as those
functions will be reusable components and part of a bigger function.

So if we don't need extra arguments, the decorator can be used without parenthesis like:
````python
import failures

@failures.scoped
def inverse_sqrt(number: str | int) -> float | None: ...
````
In next sections, we'll make use of this decorator to make our code more readable.

````{versionadded} 0.2
The decorator {func}`failures.scoped` was introduced
````