# Labeled scopes
In functions that process data through a series of sequent dependent steps,
sometimes it's not enough to handle the whole function under a single label
as it doesn't pinpoint the exact step where the failure occurred.

One solution is to use the ``Reporter.safe()`` method, as we've seen in the
reporter's section. There is also another alternative provided by ``failures``,
it's the context manager ``failures.scope``.

The difference between using ``reporter.safe(...)`` and ``failures.scope`` is that
scopes can be unbound, they do not require passing ``reporter`` to
functions as argument, yet, they still label nested failures the same
way.

## Labeling scopes
To label scopes, we evaluate its logic within the ``failures.scope``
context manager.

The syntax is like the following
```python
from failures import scope

with scope('scope-label'):
    ...  # scope instructions goes here
```

If any instruction inside the scope raises an exception, this exception
will be labeled with ``'scope-label'``.

Now let's explore the use of ``scope`` in a more concrete example,
we'll implement a function that evaluates the inverse of the square
root of a given number and round it to two decimal places.

```python
from math import sqrt
from failures import scope

def inv_sqrt(number: int | float | str) -> float:
    with scope('parse'):
        number = float(number)  # Fails for invalid number
    with scope('inverse'):
        inverse = 1 / number  # Fails for zero
    with scope('square_root'):
        sqrt_num = sqrt(inverse)  # Fails for negative numbers
    return round(sqrt_num, 2)
```
First of all, note that ``inv_sqrt`` function does not require or expects the ``reporter``
object, by its nature, this function either fails or succeeds.
And also, we execute our instructions directly inside the context scope.

The alternative using ``Reporter`` will be something like this:
```python
from math import sqrt
from failures import Reporter, REQUIRED

def inv_sqrt(number: int | float | str, reporter: Reporter) -> float:
    number = reporter('parse', REQUIRED).safe(float, number)
    inverse = reporter('parse', REQUIRED).safe(lambda: 1 / number)
    sqrt_num = reporter('parse', REQUIRED).safe(sqrt, inverse)
    return round(sqrt_num, 2)
```
The takeaway here, is that ``scope`` objects are equivalent to ``reporter``
objects with a ``REQUIRED`` marker, They always label reraise and the failure
as exception to the calling function.

This is intentional to prevent errors like ``NameError`` and ``UnboundLocalError``
in case a failure occurs, and the next instruction tries to access
the unset variable value.

### Labeled failures from nested functions
To demonstrate the real use-case of ``failures.scope``, we'll extend
the previous example to create several uncoupled functions.

```python
from math import sqrt
from failures import scope, handle


def inv_sqrt(number: int | float | str) -> float:
    with scope('parse'):
        number = float(number)  # Fails for invalid number
    with scope('inverse'):
        inverse = 1 / number  # Fails for zero
    with scope('square_root'):
        sqrt_num = sqrt(inverse)  # Fails for negative numbers
    return round(sqrt_num, 2)

def process_num(data: dict) -> float:
    with handle(lambda failure: print(f"{failure.source} : {failure.error!r}\n")):
        with scope('number'):
            with scope('extracting'):
                num = data['number']
            with scope('processing'):
                return inv_sqrt(num)
```

About the ugly nested scopes, we'll get to that soon in this section,
and the ``handle`` context, it's used to capture and handle the failure
exceptions, we'll talk about that in depth in the next section.

Now let test our ``process_num`` function.

```pycon
>>> process_num({'num': 19})
number.extracting : KeyError('number')

>>> process_num({'number': '57.8.54'})
number.processing.parse : ValueError("could not convert string to float: '57.8.54'")

>>> process_num({'number': 0})
number.processing.inverse : ZeroDivisionError('float division by zero')

>>> process_num({'number': '-16'})
number.processing.square_root : ValueError('math domain error')

>>> process_num({'number': '16'})
0.25
```

Even when ``inv_sqrt`` and ``process_num`` are completely decoupled
and can live in different modules, the failure was successfully
labeled _(like ``number.processing.square_root``)_, pinpointing
the source of failure with its error.

## Scope context reporter
The ``scope`` context manager object shares many properties with
the ``Reporter`` object, it actually uses the ``Reporter`` under the hood.

To avoid multiple nested ``with`` statements, we can use the ``scope``
internal reporter with its ``safe`` method.

The scope's reporter can be retrieved like this:

```pycon
>>> from failures import scope
>>> with scope('label') as reporter:
...     print(reporter)
Reporter('label', REQUIRED)
```

## Scope with a given reporter

## Scope with extra details

## Scoped functions

## Passing reporter to scoped function

## Scoped async functions
