# Reporting failures
The first step dealing with failures is to capture and label them, this can be done by using ``failures.Reporter``
object, in this chapter we will learn what a reporter is and how to create and use reporters in different situations. 

The ``Reporter`` api can be reviewed later in the {func}`failure.Repoeither rter` reference page.

## Creating a reporter
A reporter is created using the ``Reporter`` constructor that expects a name _(label)_ as mandatory
first _(positional-only)_ argument, each reporter has a label used to mark application failures.

````pycon
>>> from failures import Reporter
>>> reporter = Reporter('my_first_reporter')
>>> reporter
Reporter('my_first_reporter')
>>> reporter.label
'my_first_reporter'
````
This reporter can be used now for storing failures, we can demonstrate that by calling ``reporter.report(...)``
````pycon
>>> reporter.report(ValueError("this is a value error"))
>>> reporter.report(TypeError("this is a type error"))
>>> reporter.report(KeyError("this is a key error"))
>>> for failure in reporter.failures:
...   print(failure)
Failure(source='my_first_reporter', error=ValueError('this is a value error'), details={})
Failure(source='my_first_reporter', error=TypeError('this is a type error'), details={})
Failure(source='my_first_reporter', error=KeyError('this is a key error'), details={})
````
calling ``reporter.report(...)`` stores the error inside the reporter object, so it can be accessed later for handling,
it does also add some metadata like the source and additional details, the source as we said is an explicit label
that we gave our reporter, and additional details can be set as key-value information about the context and the error.

We can add details to both reporter and error, the failure will merge both details together when it reports the failure.
```pycon
>>> from failures import Reporter
>>> reporter = Reporter('my_label', environment='production', another='info')
>>> reporter.report(ValueError("this is a value error"), input=25.0)
... reporter.report(TypeError("this is a type error"), input=None, another='overriden')
... reporter.report(KeyError("this is a key error"))
>>> for failure in reporter.failures:
...   print(failure)
...
Failure(source='my_label', error=ValueError('this is a value error'), details={'environment': 'production', 'another': 'info', 'input': 25.0})
Failure(source='my_label', error=TypeError('this is a type error'), details={'environment': 'production', 'another': 'overriden', 'input': None})
Failure(source='my_label', error=KeyError('this is a key error'), details={'environment': 'production', 'another': 'info'})
```
The details that we passed to ``Reporter(...)`` are context details, they're added to every failure that ``reporter``
reports, however, specific details can be added for each failure via the ``.report(...)`` method.
If a key has been passed as context and failure-specific detail, the one passed to ``reporter.report(...)``
will override the one passed to ``Reporter(...)``.

Now before proceeding to the next section, let's make some reporter-related concepts clear.

### Failures
Failures, as shown in the previous example, are **named tuple** object that reporters use to encapsulate
errors together with their source labels and optionally some additional details.

The failure attributes can be accesses either as members ``failure.source`` or as tuple items ``failure[0]``.

More technical details can be reviewed at {func}`failures.Failure` api reference.

### Naming conventions
However, the name of the reporter is not random, it must be a non-empty string and can only contain letters,
digits, ``-`` and ``_``, like ``main``, ``evaluate_percentage``, ``func1``, ``get-item-price`` ...
Almost the same way one can name variables.
And if for some reason the reporter needs multiple labels, this is allowed by joining those labels with dots,
like ``items.counter``. 
The name can also end with parenthesis or brackets containing those the previously mentioned
characters, like ``Iteration[64]``, ``branch[main]`` or ``Inbox(new)``.

``Reporter`` will complain with a ``ValueError`` or ``TypeError`` for invalid name patterns, such as ``items..counter``,
``branch[main)``, ``-toUpper``, ``(main branch)`` ...
This validation mechanism helps to ensure a good labeling quality, as this is a main features of this library.

## Sub reporters
We can derive new reporters from an existing one the same way we create a one by ``Reporter(...)``,
this is achieved by calling the reporter itself with a new name like this
```pycon
>>> from failures import Reporter
>>> reporter = Reporter('main')
>>> sub = reporter('sub')
>>> sub
Reporter('main.sub')
>>> sub_sub = sub('sub')
>>> sub_sub
Reporter('main.sub.sub')
>>> sub_sub('another')
Reporter('main.sub.sub.another')
```
The label of new derived reporters contains the label of their parent, this behavior allows us to track the context
when we pass reporters as arguments like this.

````pycon
>>> from failures import Reporter
>>> class ClientResponseError(Exception): ...
...
>>> class JSONDecodeError(Exception): ...
...
>>> rep = Reporter('product', id='488sd1c7a', store='home_and_garden_store')
>>> rep_download = rep('download', method='GET', endpoint='https://home_and_garden_store.example.com/api/products')
>>> rep_parse = rep('parse', parser='orjson.loads')
>>> rep_download.report(ClientResponseError(404, "Product not found"))
>>> rep_parse.report(JSONDecodeError("Invalid json string"))
>>> for failure in rep.failures:
...     print(failure)
...
Failure(source='product.download', error=ClientResponseError(404, 'Product not found'), details={'id': '488sd1c7a', 'store': 'home_and_garden_store', 'method': 'GET', 'endpoint': 'https://home_and_garden_store.example.com/api/products'})
Failure(source='product.parse', error=JSONDecodeError('Invalid json string'), details={'id': '488sd1c7a', 'store': 'home_and_garden_store', 'parser': 'orjson.loads'})
````
As shown in this example, both sub-reporters include context details from their common ancestor ``details={'id': ..., 'store': ...}``
and both are labeled with ``product.(...)``.

In fact, all reporters are nodes that keep an actual reference to their ancestor. We can demonstrate this by 
the following example:

```pycon
>>> from failures import Reporter
...
>>> # Creating a reporter tree
... user_rep = Reporter('user')
... user_download = user_rep('download', method='POST')
... user_parse = user_rep('parse', type='XML')
... parse_email = user_parse('email')
... parse_phone = user_parse('phone', country='MA')
... 
>>> # Comparing labels
>>> user_rep.label
'user'
>>> user_download.label
'user.download'
>>> user_parse.label
'user.parse'
>>> parse_email.label
'user.parse.email'
>>> parse_phone.label
'user.parse.phone'
>>>
>>> # Comparing names (labels without parents)
>>> user_rep.name
'user'
>>> user_download.label
'download'
>>> user_parse.label
'parse'
>>> parse_email.label
'email'
>>> parse_phone.label
'phone'
>>>
>>> # Comparing details
>>> user_rep.details
{}
>>> user_download.details
{'method': 'POST'}
>>> user_parse.details
{'type': 'XML'}
>>> parse_email.details
{'type': 'XML'}
>>> parse_phone.details
{'type': 'XML', 'country': 'MA'}
>>>
>>> # Comparing reporter parent
>>> user_rep.parent  # None

>>> user_download.parent
Reporter('user')
>>> user_parse.parent
Reporter('user')
>>> parse_email.parent
Reporter('user.parse')
>>> parse_phone.parent
Reporter('user.parse')
>>>
>>> # Comparing reporter tree root
>>> user_rep.root  # it is the root, returns self
Reporter('user')
>>> user_download.root
Reporter('user')
>>> user_parse.root
Reporter('user')
>>> parse_email.root
Reporter('user')
```
In case the example wasn't clear, here's an explanation about the compared attributes:

+ ``label`` is a read-only property that gets the hierarchical tree labels, used in reports to pinpoint its exact
  logical location that we explicitly labeled.
+ ``name`` is a read-only property that gets only the reporter's label as a unit.
+ ``details`` is a read-only property that gets the accumulated context details that where passed to the constructors.
+ ``parent`` is a read-only property that gets the reporter which created the current one,
  root reporters return ``None``
+ ``root`` is a read-only property that gets the first reporter in the current tree, the first ancestor.

One thing to note here is that all reporters from the same tree are bound to their roots, in fact, they all share
the same failures list which can be accessed via any of them.

````pycon
>>> import failures
>>> # Creating reporter tree
>>> rep = failures.Reporter("main")
... sub = rep("sub")
... sub_sub = sub("sub_sub")
>>> # Reporting failures
>>> rep.report(TypeError("'NoneType' object is not subscriptable"))
... sub.report(TypeError("unsupported operand type(s) for /: 'NoneType' and 'int'"))
... sub_sub.report(TypeError("'NoneType' object is not callable"))
>>> # Accessing failures
>>> for failure in rep.failures:
...     print(failure)
... 
Failure(source='main', error=TypeError("'NoneType' object is not subscriptable"), details={})
Failure(source='main.sub', error=TypeError("unsupported operand type(s) for /: 'NoneType' and 'int'"), details={})
Failure(source='main.sub.sub_sub', error=TypeError("'NoneType' object is not callable"), details={})
>>> for failure in sub_sub.failures:
...     print(failure)
...
Failure(source='main', error=TypeError("'NoneType' object is not subscriptable"), details={})
Failure(source='main.sub', error=TypeError("unsupported operand type(s) for /: 'NoneType' and 'int'"), details={})
Failure(source='main.sub.sub_sub', error=TypeError("'NoneType' object is not callable"), details={})
>>> # The same list
>>> rep.failures is sub.failures
True
>>> rep.failures is sub_sub.failures
True
````

## Labeled scopes
The reporter is often used to report failures, and by reporting I mean keeping failures until the called function 
returns, and we explicitly decide to handle registered failures.

Consider a simple example, a function that takes a number, either ``str``, ``int`` or ``float`` and evaluates the square
root of its inverse, and just for demonstration purpose, we will split it into two functions.

```{code-block} python
  :caption: invsqrt.py

from math import sqrt
from failures import Reporter


def inverse_sqrt(num: str | int | float, reporter: Reporter = None) -> float | None:
    reporter = (reporter or Reporter)('inverse_sqrt')
    try:
        # [1] Fails for an invalid number
        number = float(num)
    except (ValueError, TypeError) as error:
        reporter('converting').report(error)
        return
    return _inv_sqrt(number, reporter)


def _inv_sqrt(num: float, reporter: Reporter) -> float | None:
    try:
        # [2] Fails if num == 0
        num = 1 / num
    except ZeroDivisionError as error:
        reporter('inverting').report(error)
        return
    try:
        # [3] Fails if num < 0
        num = sqrt(num)
    except ValueError as error:
        reporter('square_root').report(error)
    else:
        return round(num, 2)
```

The main function ``inverse_sqrt`` expects a valid number that can be converted to a ``float``, it doesn't require
a reporter, so we called ``(reporter or Reporter)('inverse_sqrt')``, this basically means call
``reporter('inverse_sqrt')`` if there is one or call ``Reporter('inverse_sqrt')`` otherwise.
This reporter will be the scope reporter for the next operations, then we pass it to the helper function ``_inv_sqrt``.

Now let's test our function in the interpreter:

````pycon
>>> from failures import Reporter
>>> from invsqrt import inverse_sqrt
>>> # Good cases
>>> inverse_sqrt(.25)  # float / without reporter
2.0
>>> rep = Reporter('main')
>>> inverse_sqrt(4, rep)  # int / with reporter
0.5
>>> rep.failures
[]
>>> inverse_sqrt("0.94", rep)  # str / with reporter
1.03
>>> rep.failures
[]
>>> # Bad cases
>>> rep = Reporter('main')
>>> inverse_sqrt(None, rep)  # None

>>> rep.failures.pop()
Failure(source='main.inverse_sqrt.converting', error=TypeError("float() argument must be a string or a real number, not 'NoneType'"), details={})
>>> inverse_sqrt('four', rep)  # None

>>> rep.failures.pop()
Failure(source='main.inverse_sqrt.converting', error=ValueError("could not convert string to float: 'four'"), details={})
>>> inverse_sqrt('0', rep)  # None

>>> rep.failures.pop()
Failure(source='main.inverse_sqrt.inverting', error=ZeroDivisionError('float division by zero'), details={})
>>> inverse_sqrt('-0.25', rep)  # None

>>> rep.failures.pop()
Failure(source='main.inverse_sqrt.square_root', error=ValueError('math domain error'), details={})
````
In that specific case, the reporter was misused as all steps are mandatory and dependent.
In cases like this one, we really want the function to fail and skip the remaining code,
and only handle the that failure outside. 
Returning ``None`` in this case can become buggy if the calling function expects an actual ``float``.

A better alternative in this case is to use ``Reporter`` as a failure context instead of using it as a failure reporter,
this can be achieved by using the ``with`` statement to label each part of code.

The previous code can be refactored to this

````python
from math import sqrt
from failures import Reporter


def inverse_sqrt(num: str | int | float) -> float:
    with Reporter('inverse_sqrt') as reporter:
        with reporter('converting'):
            # [1] Fails for an invalid number
            number = float(num)
        return _inv_sqrt(number)


def _inv_sqrt(num: float) -> float:
    with Reporter('inverting'):
        # [2] Fails if num == 0
        num = 1 / num
    with Reporter('square_root'):
        # [3] Fails if num < 0
        num = sqrt(num)
    return round(num, 2)
````

This already looks shorter and more readable.
All operations are scoped under specific labels, so if a failure occurs in any step,
that failure will be labeled and re-raised with context details, so the caller function needs to expect a failure.

Note here that we didn't explicitly return ``None`` when a failure occurs, nor that we needed to wrap every step in
``try/except`` blocks. 
The reporter under ``with`` statement will automatically catch and add its metadata to each failure
then re-raise it to the outer layer reporter's scope or handler.

Note also that we don't need to pass reporters between functions as arguments; the failure's metadata is passed via 
the exception.

One more thing to point out here, is that ``with Reporter('inverse_sqrt') as reporter`` returns
the ``Reporter('inverse_sqrt')`` itself, and in this specific case the reporter is not really needed as nothing will 
be reported.

So in this context, this code:
```python
...
with Reporter('inverse_sqrt') as reporter:
    with reporter('converting'):
        ...
```
Will have the same effect as this one:
```python
...
with Reporter('inverse_sqrt'):
    with Reporter('converting'):
        ...
```
Those reporters don't need to be bound.

Now, let's test this new code:

````pycon
>>> inverse_sqrt('.25')
2.0
>>> try:
...     inverse_sqrt('four')
... except Exception as exc:
...     print(exc.failure)
...
Failure(source='inverse_sqrt.converting', error=ValueError("could not convert string to float: 'four'"), details={})
>>> try:
...     inverse_sqrt(0)
... except Exception as exc:
...     print(exc.failure)
...     
Failure(source='inverse_sqrt.inverting', error=ZeroDivisionError('float division by zero'), details={})
... try:
...     inverse_sqrt(-0.0001)
... except Exception as exc:
...     print(exc.failure)
...
Failure(source='inverse_sqrt.square_root', error=ValueError('math domain error'), details={})
````
We don't need to handle raised exceptions using ``try/except`` blocks, in the next chapter we will discuss how to handle
them using ``failures.Handler``.

But this is how it can be used:

````pycon
>>> from failures import Reporter, Handler
>>> def inverse_sqrt(num):
...     with Reporter('inverse_sqrt') as reporter:
...         with reporter('converting'):
...             number = float(num)
...         ...
>>> with Handler(print):
...     inverse_sqrt("twenty five")
...
Failure(source='inverse_sqrt.converting', error=ValueError("could not convert string to float: 'twenty five'"), details={})
````

### Report or raise?
...TODO

## Execution context
When we find ourselves working with multiple inline operations, wrapping each line in ```try/except``` blocks
to capture and report failures can become tedious and ugly, let's take a look at an example:

````python
from failures import Reporter


def get_user_info(user_id: int, raw_data: dict, reporter: Reporter = None) -> tuple[int, str | None, str | None]:
  """Extracts username and email of the user with 'user_id' from 'raw_data'"""
  reporter = (reporter or Reporter)('users')
  with reporter('get_user_by_id'):
    user = raw_data['users'][user_id]
  try:
    name = user['name']
  except KeyError:
    name = None
  try:
    email = user['email']
  except KeyError as error:
    reporter('email').report(error)
    email = None
  return user_id, name, email
````
The above example is straight forward, the function ``get_user_info`` tries to get the user by id from a dictionary of 
users, then it tries to get its name and email and returns the result.

Both operations ``user['name']`` and ``user['email']`` are not critical as ``raw_data['users'][user_id]``,
as the last mentioned operation is required by the two others, and the function should fail for a non-existing
id, but failing to find the username is completely ignored and replaced by ``None`` directly, and failing to
get the email is first reported then replaced by ``None``.

We can categorize those three operations as **optional** _(like ``user['name']``)_,
**monitored** _(like ``user['email']``)_
and **required** _(like ``raw_data['users'][user_id]``)_.

However, this code is more verbose than it needs to be, and this won't be optimal if we have multiple operations.

To tackle this issue, the reporter comes with methods to execute functions inside a handled environment,
those methods are shorthands for the previous types of operations, so we can refactor our code to become like this:

```python
from failures import Reporter


def get_user_info(user_id: int, raw_data: dict, reporter: Reporter = None) -> tuple[int, str | None, str | None]:
  """Extracts username and email of the user with 'user_id' from 'raw_data'"""
  reporter = (reporter or Reporter)('users')
  user = reporter.required(lambda: raw_data['users'][user_id])
  name = reporter.optional(lambda: user['name'])
  email = reporter.safe(lambda: user['email'])
  return user_id, name, email
```

This does the exact same thing as the previous with much lesser code, ``.optional(...)`` executes a function in an
isoated environment and returns its result if it succeeds, or returns ``None`` ignoring the failure otherwise,
``.safe(...)``, it works the same way but reports the failure instead of ignoring them, and ``.required(...)``
executes a function in a labeled environment that captures, adds metadata then re-raises the failure.

All three methods have the same API, they take a callable _(mainly functions)_ as first argument, then positional 
and keyword argument that will be passed to that callable.

To demonstrate this, we can change our code and add a utility function that gets nested value by keys:
```python
from failures import Reporter


def get(data: dict, *keys):
  with Reporter('get_by_key'):
    for key in keys:
      data = data[key]
  return data

def get_user_info(user_id: int, raw_data: dict, reporter: Reporter = None) -> tuple[int, str | None, str | None]:
  """Extracts username and email of the user with 'user_id' from 'raw_data'"""
  reporter = (reporter or Reporter)('users')
  user = reporter.required(get, raw_data, 'users', user_id)
  name = reporter.optional(get, user, 'name')
  email = reporter.safe(get, user, 'email')
  return user_id, name, email
```
This feature is useful when using predefined utility functions within the reporter context instead of lambda.

```{warning}
Executing directly an instruction like ``reporter.optional(user['name'])`` will raise an exception and will not 
be handeled, we need to pass a function that reporter will call.
```

### Safe async support
Reporter also has support for asynchronous functions, same as ``.optional(...)``, ``.safe(...)`` and ``.required(...)``,
we can call and ``await`` async functions using ``.optional_async(...)``, ``.safe_async(...)`` and ``.required_async(...)``

This is an example of how to use it:

````python
from httpx import AsyncClient
from failures import Reporter

...

async def get_user(client: AsyncClient, user_id: int, *, reporter: Reporter = None):
    reporter = (reporter or Reporter)('user')
    response = await reporter('get-request').required_async(client.get, f"https://example.com/users/{user_id}")
    raw_data = reporter('parse.json').required(response.json)
    ...
````

```{note}
Async alternative methods must be awaited.
```

## Scoped functions
Usually our functions receive a reporter, either a required or an optional,
and define a top level context manager as seen in previous examples like this:
````python
def inverse_sqrt(num):
  with Reporter('inverse_sqrt'):
    with Reporter('converting'):
      number = float(num)
...
````
This makes our code ugly adding extra indentations and making us repeat the name of the function ``'inverse_sqrt'``.

To tackle this ergonomic issue, ``failures`` comes with a decorator that automates this process, it's called ``scoped``
and it can be used like this
````python
from failures import Reporter, scoped

@scoped
def inverse_sqrt(num):
  with Reporter('converting'):
    number = float(num)
...
````
This keeps the same functionality while reducing one level of indentation and names the scope based on the function's
name.

If this is not the desired behaviour, and we need our scope to have a different name than the function's,
we can override it by calling the decorator with the label as an argument like this:
````python
from failures import Reporter, scoped

@scoped('evaluating_inverse_square_root')
def inverse_sqrt(num):
  with Reporter('converting'):
    number = float(num)
...
````

Now this is nice and all, but this decorator has more purpose than being just a syntactical sugar, it also detects
and derives reporters passed as arguments to the decorated function, check this out

````pycon
>>> from failures import scoped, Reporter
... 
>>> @scoped
... def testing(*args, reporter):
...     print(reporter)
>>> rep = Reporter('main')
>>> testing(reporter=rep)
Reporter('main.testing')
>>> testing()
Reporter('testing')
````

This feature gives more flexibility to the decorated function, it may accept a reporter and internally use it to report
failures or even pass it to other _'scoped'_ functions.

In the previous example, the reporter has been passed as a required 
[keyword-only argument;](https://peps.python.org/pep-3102/) however, it can be an optional keyword-only argument
or a required or optional positional arguments like this

````pycon
>>> from failures import scoped, Reporter
>>>
>>> # reporter as a required positional argument
>>> @scoped
... def testing(_arg1, reporter):
...     print(reporter)
...
>>> testing(None, Reporter('main'))
Reporter('main.testing')
>>> testing(None)
Traceback (most recent call last):
    ...
TypeError: testing() is missing the reporter as required positional argument
>>>
>>> # reporter as an optional keyword argument
>>> @scoped
... def testing(_arg1, reporter=None):
...     print(reporter)
...
>>> testing(None, Reporter('main'))
Reporter('main.testing')
>>> testing(None)
Reporter('testing')
````

The same goes for keyword-only arguments, either optional or required,
``@scoped`` tries to detect the reporter in the function's signature following these steps in the same order:

1. It looks into parameters' annotation, if it finds a parameter hinted with ``Reporter`` like ``fun(... r: Reporter)``,
   whatever its name is, or whether it's a positional or keyword parameter, it supposes that is a reporter.
2. If no type hint is found, the decorator tries to find the name ``'reporter'`` with no annotation, and supposes that
   is the reporter, unless it has an annotation hinting another type, like ``reporter: HTMLReporter``.

If the parameter has a default value other than ``Reporter(...)`` or ``None``, it is no longer considered a reporter.

But if all those conditions are met, and that argument is not an instance of ``failures.Reporter`` or ``None``
at runtime, a type error will be raised.
