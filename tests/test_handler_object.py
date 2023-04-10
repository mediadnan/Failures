# ---------   Scope handler test specifications    --------------------------------------------#

#   Test handler() creation
#       + with no arguments [IMPLEMENTED]
#       + with normal function handler [IMPLEMENTED]
#       + with predefined Handler [IMPLEMENTED]
#       + with nested Handler objects [IMPLEMENTED]

#   Test handler() with filters (combine cases) [IMPLEMENTED]
#                           ___________________________________
#                           | Failure                         |
#                           | Failures (with failure objects) |
#                           | Failures (with failures objects)|
#                           ___________________________________
#       _____________________________________   _________________________________________
#       | ignore nothing                    |   | propagate nothing                     |
#       | ignore one type of exceptions     |   | propagate one type of exceptions      |
#       | ignore multiple type exceptions   |   | propagate multiple type exceptions    |
#       _____________________________________   _________________________________________

#   Test combine nested handlers [IMPLEMENTED]
#       > Unwrap handling function
#       > Combine and optimize filters

#   Test handler validation
#       + validate filters  [TODO]
#       + validate handler  [TODO]

# ---------------------------------------------------------------------------------------------#

import pytest
import itertools
from typing import Union, List
import failures
from failures.core import Failures, Failure  # needed by eval(...)


def unwrap_failure(failure: Union[Exception, Failures, Failure]) -> List[Exception]:
    if isinstance(failure, Failures):
        return list(itertools.chain(*map(unwrap_failure, failure.failures)))
    elif isinstance(failure, Failure):
        return [failure.error]
    return [failure]


@pytest.mark.parametrize("handler_func", [
    "nothing",
    "handler",
    "failures.handler(handler)",
    "failures.handler()",
    "failures.handler(failures.handler(failures.handler(handler)))",
])
def test_handler_creation(handler, handler_func):
    failures_handler = failures.handler(eval(handler_func)) if handler_func != "nothing" else failures.handler()
    assert isinstance(failures_handler, failures.core.Handler)


@pytest.mark.parametrize("failure, errors", [
    (Failure('source', ValueError('test')), (ValueError,)),
    (Failure('source', KeyError('test')), (KeyError,)),
    (Failure('source', IndexError('test')), (IndexError,)),
    (Failure('source', TypeError('test')), (TypeError,)),
    (Failures(Failure('source', ValueError('test')),
              Failure('source', KeyError('test')),
              Failure('source', IndexError('test')),
              Failure('source', TypeError('test'))),
     (ValueError, KeyError, IndexError, TypeError)),
    (Failures(Failures(Failure('source', ValueError('test')),
                       Failure('source', KeyError('test'))),
              Failures(Failure('source', IndexError('test')),
                       Failure('source', TypeError('test')))),
     (ValueError, KeyError, IndexError, TypeError))
], ids=str)
@pytest.mark.parametrize("ignore_filter, ignored_errors", [
    (None, ()),
    ((), ()),
    (KeyError, (KeyError,)),
    ((KeyError,), (KeyError,)),
    ((KeyError, IndexError), (KeyError, IndexError)),
], ids=str)
@pytest.mark.parametrize("propagate_filter, propagated_errors", [
    (None, ()),
    ((), ()),
    (ValueError, (ValueError,)),
    ((ValueError,), (ValueError,)),
    ((ValueError, TypeError), (ValueError, TypeError)),
], ids=str)
def test_handler_with_filters(
        handler,
        failure,
        errors,
        ignore_filter,
        ignored_errors,
        propagate_filter,
        propagated_errors
):
    failures_handler = failures.handler(handler, ignore=ignore_filter, propagate=propagate_filter)
    try:
        failures_handler(failure)
    except Exception as error:
        assert propagated_errors, f"{error!r} raise but unexpected"
        for propagated in unwrap_failure(error):
            assert isinstance(propagated, propagated_errors), f"{error!r} raise but unexpected"
    for handled in map(type, handler.errors):
        assert issubclass(handled, errors), f"{handled!r} handled without being raised"
        if ignored_errors:
            assert not issubclass(handled, ignored_errors), f"{handled!r} must be ignored"


def test_handler_optimization(handler):
    nested = failures.handler(
        failures.handler(
            failures.handler(handler, propagate=ValueError),
            ignore=ImportError, propagate=(ValueError, KeyError)
        ), ignore=(TypeError, ValueError, IndentationError)
    )
    assert nested.handler_function is handler
    assert (len(nested.ignore) == 4 and
            isinstance(nested.ignore, tuple) and
            set(nested.ignore) == {ImportError, TypeError, ValueError, IndentationError})
    assert (len(nested.propagate) == 2 and
            isinstance(nested.propagate, tuple) and
            set(nested.propagate) == {ValueError, KeyError})
