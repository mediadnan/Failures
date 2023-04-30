(handling)=
# Handling failures
Collecting failures related to an application action is only done
to process and analyze them later than take some action based on that.

How to handle failures is totally up to the library user and depends on the type of the failure, 
``failures`` however, provides tools to help process them easily.

## Failure handling function
In simple terms, the failure handler is just a function _(or callable in general)_ that takes a {class}`failures.Failure`
object as the only _(positional)_ argument and is expected to return nothing. 
In other words, it should have this signature ``(Failure) -> None``.

Async functions are not supported yet by ``failures``, if an async action is required, the user must process, prepare
and store failures as an intermediate action then do some asynchronous action implemented by the user.

By default, and as a placeholder handler, ``failures`` comes with default handler {func}``failures.print_failure``
that prints the failure information as logs to the standard output.

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
TODO / default handler
TODO / override default handler

## Filtered handler

### Filter by label

TODO / Handling failures with specific label

### Filter by label pattern

TODO / Handling failures with a specific label pattern

### Filter by error type

TODO / Handling failures from specific error type or types

### Filter by severity

TODO / Handling failures with specific severity

### Combining filters

TODO / filtering by any of multiple filters
TODO / filtering by a combination of filters
TODO / combining filters with logical 'OR' and 'AND'

## Combining multiple handlers

## Handling from reporter
