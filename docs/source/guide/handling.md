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
>>> from failures import filtered, Reporter
>>> # This filter will only handle failures with ValueError (or subclass) error instances
... handler_func = filtered(print, ValueError)
>>> # This one will handle failures with errors either of TypeError or ValueError types
... handler_func2 = filtered(print, ValueError, TypeError)
>>> rep = Reporter("testing_filtered")
>>> rep.report(Exception("generic error"))
>>> rep.report(ValueError("value error"))
>>> rep.report(TypeError("type error"))
>>> for failure in rep.failures:
...     handler_func(failure)
...
Failure(source='testing_filtered', error=ValueError('value error'), details={})
>>> for failure in rep.failures:
...     handler_func2(failure)
...
Failure(source='testing_filtered', error=ValueError('value error'), details={})
Failure(source='testing_filtered', error=TypeError('type error'), details={})
````

Or passing a filtered handler as tuple to the {class}`failures.Handler` constructor like this

````pycon
>>> from failures import Handler, Reporter
>>> handler = Handler((print, ValueError))
>>> handler2 = Handler((print, (ValueError, TypeError)))
>>>
>>> rep = Reporter("testing_filtered")
>>> rep.report(Exception("generic error"))
>>> rep.report(ValueError("value error"))
>>> rep.report(TypeError("type error"))
>>> handler.from_reporter(rep)
Failure(source='testing_filtered', error=ValueError('value error'), details={})
>>> handler2.from_reporter(rep)
Failure(source='testing_filtered', error=ValueError('value error'), details={})
Failure(source='testing_filtered', error=TypeError('type error'), details={})
>>>
>>> with handler:  # Handles only ValueError
...     with rep:
...         raise TypeError("ignored")
...

>>> with handler2:  # Handles only ValueError
...     with rep:
...         raise TypeError("ignored")
...
Failure(source='testing_filtered', error=TypeError('ignored'), details={})
````

````{note}
Note that unlike ``filtered()``, multiple filters are wrapped in a tuple when using ``Handler()``
````

### Filter by label
We can handle a specific labeled failure by a custom handler, this is done by passing the handler together with a label
to the {class}`failures.Handler` _(or {func}`failures.filtered`)_

````pycon
>>> from failures import Reporter, Handler
>>> # Reporter tree
>>> root = Reporter("root")
>>> proc1 = root("process1")
>>> proc2 = root("process2")
>>> # Reporting errors
>>> root.report(Exception("from root"))
>>> proc1.report(Exception("from proc1"))
>>> proc2.report(Exception("from proc2"))
>>> # Checking reported
>>> for _failure in root.failures:
...     print(failure)
...     
Failure(source='root', error=Exception('from root'), details={})
Failure(source='root.process1', error=Exception('from proc1'), details={})
Failure(source='root.process2', error=Exception('from proc2'), details={})
>>> def custom(failure):
...     print(f"(*)custom failure => source: {failure.source}, error: {failure.error!r}")
...
>>> Handler((custom, "root.process1"), print).from_reporter(root)
Failure(source='root', error=Exception('from root'), details={})
(*)custom failure => source: root.process1, error: Exception('from proc1')
Failure(source='root.process1', error=Exception('from proc1'), details={})
Failure(source='root.process2', error=Exception('from proc2'), details={})
````

As shown in this example, ``print()`` was called with all reported failures, but ``custom()`` was only called for
the failure labeled exactly ``'root.process1'``. 
This can be useful to control which function handles which failure, but implementing a handler to handle one single 
failure is rarely the desired behaviour, we can target a group of labels using the wildcard symbol ``*``.

If we want to process all failures under ``'root'`` label but not ``'root'`` itself, we can filter by
``"root.*"``

````pycon
...
>>> Handler((custom, "root.*")).from_reporter(root)
(*)custom failure => source: root.process1, error: Exception('from proc1')
(*)custom failure => source: root.process2, error: Exception('from proc2')
````

The wildcard symbol ``*`` matches everything, it can be placed anywhere it's needed

````pycon
...
>>> Handler((custom, "*process*")).from_reporter(root)
(*)custom failure => source: root.process1, error: Exception('from proc1')
(*)custom failure => source: root.process2, error: Exception('from proc2')
````

````{note}
This ``Handler((handle, '*'))`` is the  same as this ``Handler(handle)``
````

### Filter by error type
Failures can be filtered by exception type, this is achieved by passing the exception type itself with the handler

````pycon
>>> from failures import Handler, Reporter
>>> handler = Handler(
...     ((lambda f: print(f"[handler 1] :: {f!r}")), (KeyError, IndexError)),
...     ((lambda f: print(f"[handler 2] :: {f!r}")), (ValueError, TypeError)),
... )
>>> reporter = Reporter("filtering_by_exctype")
>>> for ErrType in (KeyError, IndexError, ValueError, TypeError, NameError, RecursionError):
...     reporter.report(ErrType("test err"))
...
>>> handler.from_reporter(reporter)
[handler 1] :: Failure(source='filtering_by_exctype', error=KeyError('test err'), details={})
[handler 1] :: Failure(source='filtering_by_exctype', error=IndexError('test err'), details={})
[handler 2] :: Failure(source='filtering_by_exctype', error=ValueError('test err'), details={})
[handler 2] :: Failure(source='filtering_by_exctype', error=TypeError('test err'), details={})
````

````{note}
This ``Handler((handle, Exception))`` is the  same as this ``Handler(handle)``
````

### Combining filters
Filters can be as specific as we need them to be, we can combine multiple filters to match the specification, 
and different types of filters can be combined too:

Consider this list of failures

````pycon
>>> from failures import Handler, Failure
>>> failures = [
...     Failure("app.trigger", RuntimeError("..."), {}),
...     Failure("client.data.download", TimeoutError("..."), {}),
...     Failure("client.data.process.decode", ValueError("..."), {}),
...     Failure("client.data.process.extract", KeyError("..."), {}),
...     Failure("client.data.process.analyze", TypeError("..."), {}),
...     Failure("client.data.store", IOError("..."), {}),
...     Failure("app.notify", TypeError("..."), {}),
... ]
````



TODO / filtering by any of multiple filters
TODO / filtering by a combination of filters
TODO / combining filters with logical 'OR' and 'AND'

## Combining multiple handlers

