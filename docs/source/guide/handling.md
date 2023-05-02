(handling)=
# Handling failures
Collecting failures related to an application action is only done
to process and analyze them later, then take some action based on that.

How to handle failures however, is totally up to the library user and depends on the type of the failure, 
``failures`` just provides tools to help process them easily.

## Failure handling function
In simple terms, the failure handler is just a function _(or callable in general)_ that takes a {class}`failures.Failure`
object as the only _(positional)_ argument and is expected to return nothing. 
In other words, it should have this signature ``(Failure) -> None``.

Async functions are not yet supported by ``failures`` as handlers, if required, the user must prepare and store failures
as an intermediate action then do some asynchronous action implemented by the user.

By default, and as a placeholder handler, ``failures`` comes with {func}``failures.print_failure``
that prints the failure to the standard output with the date it was registered.

````pycon
>>> from failures import Reporter, print_failure
>>> reporter = Reporter('testing_default_handler')
>>> reporter.report(Exception("Generic error"))
>>> failure = reporter.failures[0]
>>> print_failure(failure)
[FAILURE] testing_default_handler :: Exception(Generic error) 2023-04-30 20:00:00
````

We can implement our own handler
````pycon
>>> from logging import getLogger, basicConfig
>>> from failures import Reporter, Failure
>>> basicConfig(format="%(name)s: %(message)s [%(asctime)s]")
>>> def handler(failure: Failure) -> None:
        source, error, details = failure
...     getLogger(source).error(f"{error = !r} {details = !r}")
>>> reporter = Reporter('testing_default_handler')
>>> reporter.report(Exception("Generic error"), input=22)
>>> handler(reporter.failures[0])
testing_default_handler: error = Exception('Generic error') details = {'input': 22} [2023-04-30 20:00:00,399]
````

The failure object failure can be interpreted as tuple or as object, so the failure's source can be accessed 
like ```failure.source``` or like ``failure[0]``, the same for error, either ``failure.error`` or ``failure[1]`` ...

## Handle context
For more complex use-cases, like filtering and choosing which failures to handle and which function to use for each,
a function as handler can become a bit harder to maintain.

A wrapper object {class}`failures.Handler` can be used to organize handlers and catch raised failures,
the constructor can take multiple handler functions like ``Handler(fun1, fun2, ...)`` if needed, the handler object
will call them the same order they were inserted for each failure; 

````pycon
>>> from failures import Failure, Handler
>>> failure = Failure('reporter_name', Exception('test error'), {})
>>> stored = []
>>> def store_failure(_failure: Failure) -> None:
...     stored.append(_failure)
...
>>> handler = Handler(print, store_failure)
>>> handler(failure)    # handle failure
Failure(source='reporter_name', error=Exception('test error'), details={})
>>> stored
[Failure(source='reporter_name', error=Exception('test error'), details={})]
>>> # Handler with default handler
>>> handler2 = Handler()
>>> handler2(failure)
[FAILURE] reporter_name :: Exception(test error) 2023-05-02 08:00:00
````
If the constructor ``Handler()`` is called without arguments, it will use {func}`print_failure` as its only handler.

The handler can process failures directly from the reporter using the {meth}`Handler.from_reporter` method,
it automatically iterates over the reporter's registered failures.

````pycon
>>> from failures import Reporter, Handler
>>> reporter = Reporter('testing_handler')
>>> def fail(msg: str):
...     raise Exception(msg)
...
>>> with Handler(print) as handler:
...     reporter.safe(fail, "error 1")
...     reporter.safe(fail, "error 2")
...     reporter.required(fail, "error 3")  # this is the last step
...     reporter.safe(fail, "will never be registered")
...
Failure(source='testing_handler', error=Exception('error 3'), details={})
>>> handler.from_reporter(reporter)
Failure(source='testing_handler', error=Exception('error 1'), details={})
Failure(source='testing_handler', error=Exception('error 2'), details={})
````

## Filtered handler
Handlers can target only a specific group of failures, we can make different handlers for different groups of failures,
and this is done by specifying a filter together with the handler when creating the {class}`failures.Handler` object.

Failures can be filtered by source label or by exception type, in the next sections we will talk about them.  

The filtered handlers can be made using {func}`failures.filtered` function like this

````pycon
>>> from failures import filtered
>>> handler_func = filtered(print, ValueError)
>>> # This filter will only handle failures with ValueError (or subclass) error instances
>>> handler_func2 = filtered(print, ValueError, TypeError)
>>> # This one will handle failures with errors either of TypeError or ValueError types
````

Or passing a filtered handler as tuple to the {class}`failures.Handler` constructor like this

````pycon
>>> from failures import Handler
>>> handler = Handler((print, ValueError))
>>> handler2 = Handler((print, ValueError, TypeError))
````

### Filter by label


### Filter by label pattern

TODO / Handling failures with a specific label pattern

### Filter by error type

TODO / Handling failures from specific error type or types

### Combining filters

TODO / filtering by any of multiple filters
TODO / filtering by a combination of filters
TODO / combining filters with logical 'OR' and 'AND'

## Combining multiple handlers

## Handling from reporter
