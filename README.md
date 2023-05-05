<div id="readme_header" style="text-align: center">
<h1 style="color: #913946ff; font-family: Candara, sans-serif;">Failures</h1>
<p style="color: #bf6572; font-family: Candara, sans-serif; font-style: italic">Successfully dealing with failures</p>
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

## Usage
This example will show the tip of the iceberg, for a more complete tutorial refer to the documentation page at
[documentation page](https://failures.readthedocs.org).

``failures`` contains two main objects, ``Reporter`` and ``Handler``, the first one gathers all failures and the second
on processes them.

Let's define some utilities for this example in a file named ``defs.py``

````python
# defs.py
import json
from typing import Any
from dataclasses import dataclass
from failures import Reporter, Handler, Failure, scoped

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

def get_user(user_id: str) -> User:
    reporter = Reporter('user')
    with reporter('retrieve', id=user_id):
        raw_json = _database[user_id]
    with reporter('json_decode'):
        user_data = json.loads(raw_json)
    return convert(user_id, user_data, reporter)

@scoped
def convert(_id: str, _data: dict[str, Any], reporter: Reporter) -> User:
    return User(
        id=_id,
        name=reporter.required(lambda: _data['name']),
        email=reporter.safe(_data.__getitem__, 'email'),
        phone=reporter.optional(_data.__getitem__, 'phone')
    )

def not_found_404(failure: Failure) -> None:
    pass

handler = Handler((not_found_404, "*.retrieve"), print, )

````
