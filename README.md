<div id="readme_header" style="text-align: center">
<h1 style="color: #913946ff; font-family: Candara, sans-serif;">Failures</h1>
<p style="color: #bf6572; font-family: Candara, sans-serif; font-style: italic">Successfully dealing with failures</p>
<br/>
<a href="https://github.com/mediadnan/Failures/actions/workflows/test.yml" target="_blank"><img src="https://github.com/mediadnan/Failures/actions/workflows/test.yml/badge.svg" alt="Tests"/></a>
<a href="https://codecov.io/gh/mediadnan/Failures" target="_blank"><img src="https://codecov.io/gh/mediadnan/Failures/branch/main/graph/badge.svg?token=E58PJ3OFME" alt="CodeCov"/></a>
<a href="https://www.python.org/downloads/" target="_blank"><img src="https://img.shields.io/pypi/pyversions/failures" alt="PyPI - Python Version"/></a>
<a href="https://failures.readthedocs.io/" target="_blank"><img alt="Read the Docs" src="https://img.shields.io/readthedocs/failures"></a>
<a href="https://en.wikipedia.org/wiki/MIT_License" target="_blank"><img src="https://img.shields.io/github/license/mediadnan/failures" alt="License"/></a>
<a href="https://github.com/mediadnan/Failures/issues" target="_blank"><img src="https://img.shields.io/github/issues/mediadnan/failures" alt="GitHub issues" /></a>
<a href="https://pypi.org/project/failures/" target="_blank"><img alt="PyPI - Downloads" src="https://img.shields.io/pypi/dm/failures"></a>
</div>

## What is failures
This library simplifies dealing with application failures especially when using multiple nested components
that process some data and could fail at any point.

Often in production, the app must be robust enough against errors but still report them so we can improve it regularly,
this requires us as developers to isolate those operations _(usually within ``try...except`` blocks)_ then catch
any possible errors to report them and provide an alternative result _(like returning ``None``)_.
This is an additional job to be done to keep achieve the production robustness.

Meanwhile, this library suggests some tools to ease this process and divides it into two main phases, 
the first is capturing failures through an application action and between function calls while giving them
meaningful labels and optionally explicit metadata to help us understand them later and their context,
the second phase is to process those collected failures with the ability to filter and choose different
handling action for different type of failures.

The library focuses on two main factors, simplicity and performance, by keeping the syntax easy, clean and intuitive
for a better and more readable code, and by optimizing its code to minimize the impact on your application.

## Installation
``failures`` is available at PyPI, it requires python 3.8 or higher, to install it run the ``pip`` command:

```shell
pip install failures
```

## Example
This example will show the tip of the iceberg, for a more complete tutorial refer to the documentation page at
[documentation page](https://failures.readthedocs.org).

``failures`` contains two main objects, ``Reporter`` and ``Handler``, the first one gathers all failures and the second
on processes them.

Let's define some utilities for this example in a file named ``defs.py``

````python
import json
import logging
from dataclasses import dataclass
from failures import Reporter, Handler, Failure

_database = {
    '692999103396568d': b'{"name": "alertCheetah2", "email": "alertCheetah2@example.com", "phone": "(+212)645-882-425"}',
    'e2ddc4f976f8ccf8': b'{"name": "ardentJaguar0", "phone": "(+212)611-962-964"}',
    'd097eba4d97a1ce0': b'{"name": "tautWeaver8", "email": "tautWeaver8@example.com", "phone": "(+212)683-480-745"}',
    'ef0eb816db00f939': b'{"name": "awedPolenta7", "email": "awedPolenta7@example.com", "phone": "(+212)641-014-059"}',
    'b54c8bea6badd65d': b'{"name": "dearCod2", "email": "dearCod2@example.com", "website": "www.dearCod2.example.com"}',
    'bad-8394313d4c44': b'{"name": "panickyViper9", "ema'
}

@dataclass
class User:
    id: str
    name: str
    email: str | None
    phone: str | None

def not_found_404(failure: Failure) -> None:
    try:
        user_id = failure.details['id']
    except KeyError:
        return
    logging.getLogger(failure.source).error(f"No user found with id = {user_id!r}", exc_info=failure.error)

handler = Handler((not_found_404, "*.retrieve"), print)

def get_user(user_id: str) -> User | None:
    reporter = Reporter('user')
    with handler:
        with reporter('retrieve', id=user_id):
            raw_json = _database[user_id]
        with reporter('json_decode'):
            user_data = json.loads(raw_json)
        rep_get = reporter('get', data=user_data)
        user = User(
            id=user_id,
            name=rep_get('name').required(lambda: user_data['name']),
            email=rep_get('email').safe(user_data.__getitem__, 'email'),
            phone=rep_get('phone').optional(user_data.__getitem__, 'phone')
        )
        handler.from_reporter(reporter)
        return user
````

### Code explained
We declared a dummy data collection ``_database`` to act as a database, then we defined a data class ``User``
to wrap user data.

We define then a custom handler ``not_found_404`` to be called only when a user is not found, this handler takes
a ``Failure`` object and returns nothing, all handlers should have this same signature.

Then we create a ``Handler`` object used to handle application failures, we pass the custom handler under a condition
``'*.retrieve'``, the condition means every label that ends with ``'retrieve'`` like in this case ``'user.retrieve'``. 

After that we define our main action ``get_user(user_id: str) -> User | None`` that takes an id and returns a user if
it exists, we evaluate all its instructions within the handler context to capture failures, then we create the root
reporter labeled ``'user'``, all following operations will be labeled ``user.(somthing)``, then we try to retrieve
a user by id ``_database[user_id]``, and as this might potentially fail, we execute it inside the reporter's context
under the label ``retrieve``, this context is holding the ``user_id`` as additional detail.
Using the reporter as context manager ``with reporter:`` ensures that the functions returns directly to the handler in 
case of failure, the next code won't be executed.
The same for the next instruction, we wrap it into a labeled scope ``json_decode`` to label it and mark it as required
step.

Then we create a ``User`` object, this time using inline reporter context, there is three; ``reporter.required(...)``
for mandatory operations and it's the same as ``with reporter: ...``, it stops and returns to the handler in case 
of failure, ``reporter.safe(...)`` does capture and keep the failure to be processed later and returns ``None`` as 
alternative result, and ``reporter.optional(...)`` does the same but without reporting the failure.
All the three expect a callable with or without parameters to be called so ``reporter.safe(func, 1, 2, a=3, b=4)``
executes ``func(1, 2, a=3, b=4)`` in isolation.

After that and finally we process those reported failures and return the result.

### Usage
Now let's jump into the interpreter and load our function and start calling it with different ids:

````pycon
>>> from defs import get_user
>>> # Existing users
>>> get_user('692999103396568d')
User(id='692999103396568d', name='alertCheetah2', email='alertCheetah2@example.com', phone='(+212)645-882-425')

>>> get_user('e2ddc4f976f8ccf8')  # Missing email reported and handled with print(failure)
Failure(source='user.get.email', error=KeyError('email'), details={'data': {'name': 'ardentJaguar0', 'phone': '(+212)611-962-964'}})
User(id='e2ddc4f976f8ccf8', name='ardentJaguar0', email=None, phone='(+212)611-962-964')

>>> get_user('d097eba4d97a1ce0')
User(id='d097eba4d97a1ce0', name='tautWeaver8', email='tautWeaver8@example.com', phone='(+212)683-480-745')

>>> get_user('ef0eb816db00f939')
User(id='ef0eb816db00f939', name='awedPolenta7', email='awedPolenta7@example.com', phone='(+212)641-014-059')

>>> get_user('b54c8bea6badd65d')  # Missing phone number ignored
User(id='b54c8bea6badd65d', name='dearCod2', email='dearCod2@example.com', phone=None)

>>> # Bad json format
>>> get_user('bad-8394313d4c44')  # returns None
Failure(source='user.json_decode', error=JSONDecodeError('Unterminated string starting at: line 1 column 27 (char 26)'), details={})

>>> # Non-existing users
>>> get_user('random-id')
ERROR:user.retrieve:No user found with id = 'random-id'
Traceback (most recent call last):
  File "/path/to/defs.py", line 35, in get_user
KeyError: 'random-id'
Failure(source='user.retrieve', error=KeyError('random-id'), details={'id': 'random-id'})

````
