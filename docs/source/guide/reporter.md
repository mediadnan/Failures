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
In that specific case, the reporter is not really needed as all steps are mandatory.
In cases like this one, we really want to fail to skip the remaining code and only handle the failure outside, even
returning ``None`` in this case can become buggy if the calling function expects an actual ``float``.

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
        return _inv_sqrt(number, reporter)


def _inv_sqrt(num: float) -> float:
    with Reporter('inverting'):
        # [2] Fails if num == 0
        num = 1 / num
    with Reporter('square_root'):
        # [3] Fails if num < 0
        num = sqrt(num)
    return round(num, 2)
````

TODO ...

\
\
To refactor 

## Safe context
When we find ourselves working multiple inline operations, trying to manually wrap each one in ```try...except``` blocks
then capture and report each failure can be tedious.

````python
from dataclasses import dataclass
from failures import Reporter, REQUIRED, OPTIONAL

@dataclass
class User:
    id: int
    name: str
    email: str | None
    phone: str | None

def parse_user(data: dict, reporter: Reporter) -> User:
    try:
        user_id = int(data['user']['id'])
    except (KeyError, TypeError, ValueError) as err:
        reporter('user.id', REQUIRED).report(err)
    try:
        user_name = data['user']['personal']['name']
    except (KeyError, TypeError) as err:
        reporter('user.name', REQUIRED).report(err)
    try:
        user_email = data['user']['contact']['email']
    except (KeyError, TypeError) as err:
        reporter('user.email').report(err)
        user_email = None
    try:
        user_phone = data['user']['contact']['phone']
    except (KeyError, TypeError) as err:
        reporter('user.phone', OPTIONAL).report(err)
        user_phone = None
    return User(user_id, user_name, user_email, user_phone)
````

This example is self-explanatory,
we're extracting user data from a raw data source and returning a well-structured object.
We want to raise a failure exception if id or name are missing, so we marked those operations as required,
and we want to ignore missing phone numbers and email substituting them by ``None`` in case of their absence,
but we want to still report missing emails.

But seriously, this code was very ugly even with just 4 operations.

The reporter provides a shorthand method to automate calling all of this, the ``Reporter.safe`` method.

We can refactor the previous function to become:

````python
from dataclasses import dataclass
from failures import Reporter, REQUIRED, OPTIONAL

@dataclass
class User:
    id: int
    name: str
    email: str | None
    phone: str | None

def parse_user(data: dict, reporter: Reporter) -> User:
    reporter = reporter('user')
    user_id = reporter('id', REQUIRED).safe(lambda: int(data['user']['id']))
    user_name = reporter('name', REQUIRED).safe(lambda: data['user']['personal']['name'])
    user_email = reporter('email').safe(lambda: data['user']['contact']['email'])
    user_phone = reporter('phone', OPTIONAL).safe(lambda: data['user']['contact']['phone'])
    return User(user_id, user_name, user_email, user_phone)
````
Now it looks less ugly while returning the same result.

````{note}
The ``safe`` methed takes a callable as first argumen, for that reason we created an annonymous ``lambda`` function, 
any remaining arguments will be passed directly to that callable.
````

Alternatively, we could use a utility function that extracts from dictionaries like

````python
def extract(source: dict, *keys: Any, cast: Callable[[Any], Any] = None) -> Any:
    for key in keys:
        source = source[key]
    if callable(cast):
       return cast(source)
    return source

def parse_user(data: dict, reporter: Reporter) -> User:
    ...
    user_id = reporter('id', REQUIRED).safe(extract, data, 'user', 'id', cast=int)
    user_name = reporter('email', REQUIRED).safe(extract, data, 'user', 'personal', 'name')
    ...
````

### Safe async support
To evaluate asynchronous functions inside a safe context, we can use ``Reporter.safe_async()`` method,
this will await the coroutine inside the context to catch any exception.

This is an example of how to use it:

````{code-block} python
:emphasize-lines: 15

from dataclasses import dataclass
from httpx import AsyncClient
from failures import Reporter, REQUIRED, OPTIONAL

@dataclass
class User:
    id: int
    name: str
    email: str | None
    phone: str | None


async def get_user(user_id: int, client: AsyncClient, reporter: Reporter) -> User:
    reporter = reporter('user')
    response = await reporter('request.get', REQUIRED).safe_async(client.get, f"https://api.example.com/users/{user_id}")
    raw_data = reporter('parse.json', REQUIRED).safe(response.json)
    reporter = reporter('extract')
    user_id = reporter('id', REQUIRED).safe(lambda: int(raw_data['user']['id']))
    ...
````
