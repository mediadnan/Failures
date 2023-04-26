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
>>> reporter.report(TypeError("this is a type error"), input=None, another='overriden')
>>> reporter.report(KeyError("this is a key error"))
>>> for failure in reporter.failures:
...   print(failure)
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
We can derive new reporters from an existing one the same way we create one,
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

We can keep deriving sub reporters as much as we need, like:

````pycon
>>> sub_sub = sub_reporter('sub')
>>> sub_sub
Reporter('main.sub.sub', NORMAL)
>>> sub_sub('sub_again')
Reporter('main.sub.sub.sub_again', NORMAL)
````
And this will help us when passing reporters to functions as arguments,
as they keep track of their origin. Making them the perfect tool to pinpoint
the source of the failure.

Now let's explore some common reporter properties and compare them

```pycon
>>> # reporter's label
>>> reporter.label
'main'
>>> sub_reporter.label
'main.sub'
>>> sub_sub.label
'main.sub.sub'
>>> # reporter's parent
>>> reporter.parent  # None

>>> sub_reporter.parent
Reporter('main', NORMAL)
>>> sub_sub.parent
Reporter('main.sub', NORMAL)
>>> # reporter's root
>>> reporter.root  # self
Reporter('main', NORMAL)
>>> sub_reporter.root
Reporter('main', NORMAL)
>>> sub_sub.root
Reporter('main', NORMAL)
>>> # reporter's name
>>> reporter.name
'main'
>>> sub_reporter.name
'sub'
>>> sub_sub.name
'sub'
```

As shown in this example, the ``label`` property gets the full combined tree names of the reporter, 
the ``name`` property only gets the current reporter's name, the ``parent`` property returns
the reporter's parent if there is one and the ``root`` property returns the first reporter
of the tree.

The main reason reporters are made is to report failures; we can report from any of the three reporters

````pycon
>>> reporter.report(TypeError('test type error'))
>>> sub_reporter.report(Exception('test generic error'))
>>> sub_sub.report(TabError('test error error'))
>>> for failure in reporter.failures:
...     print(failure)
Failure(source='main', error=TypeError('test type error'), details={}, severity=<Severity.NORMAL: 1>)
Failure(source='main.sub', error=Exception('test generic error'), details={}, severity=<Severity.NORMAL: 1>)
Failure(source='main.sub.sub', error=TabError('test error error'), details={}, severity=<Severity.NORMAL: 1>)
````

All failures will be inserted to the same shared list.

````pycon
>>> reporter.failures is sub_reporter.failures
True
>>> reporter.failures is sub_sub.failures
True
````

## Operation severities
The reporter has three different states, ``REQUIRED``, ``NORMAL`` or ``OPTIONAL``, as shown in previous examples,
the default state is ``NORMAL``.

Sometimes a failure is quite expected, like trying to access an optional key from a dictionary that could be missing,
as this failure is often happening, reporters with ``NORMAL`` flag will annoyingly report it every time it happens.
If we want to ignore that specific failure, we can mark that specific reporter as ``OPTIONAL``.

We can override the default severity flag by passing the new one as second argument.

````pycon
>>> from failures import Reporter, OPTIONAL, NORMAL, REQUIRED
>>> reporter = Reporter('main', OPTIONAL)  # default is NORMAL for the first one
>>> reporter
Reporter('main', OPTIONAL)
>>> reporter.severity
<Severity.OPTIONAL: 0>
>>> sub = reporter('sub', OPTIONAL)  # default is NORMAL
>>> sub
Reporter('main.sub', OPTIONAL)
>>> sub.severity
<Severity.OPTIONAL: 0>
>>> sub_sub = sub('sub')  # keeping the default
>>> sub_sub
Reporter('main.sub.sub', NORMAL)
>>> # reporting from each one
>>> reporter.report(Exception("test failure 1"))
>>> sub.report(Exception("test failure 2"))
>>> sub_sub.report(Exception("test failure 3"))
>>> for failure in reporter.failures:
...     print(failure)
Failure(source='main.sub.sub', error=Exception('test failure 3'), details={}, severity=<Severity.NORMAL: 1>)
````
However, some operations can be a dependency for the next ones, as important as they are, we want 
to skip the rest of operations and raise an error informing the caller that the whole operation has failed.
To achieve this, we can mark the reporter of that specific operation as ``REQUIRED``

````pycon
>>> reporter = Reporter('main', REQUIRED)
>>> reporter.report(Exception("testing"))
Traceback (most recent call last):
    ...
failures.core.FailureException: ('main', Exception('testing'), Reporter('main', REQUIRED))
>>> sub = reporter('sub', REQUIRED)
>>> sub.report(ValueError('testing'))
Traceback (most recent call last):
    ...
failures.core.FailureException: ('main.sub', ValueError('testing'), Reporter('main.sub', REQUIRED))
````

That failure exception was intentionally raised, to stop any remaining code and to be captured by the outermost
calling layer. 
We will discuss how to handle that in a later section.

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
